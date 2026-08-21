"""Platform-specific filesystem locations and legacy-directory migration.

Storage uses an immutable application identifier rather than the display name.
This prevents another application named ClipLM from sharing our settings or
database directories. The identifier remains stable even if the project website
or GitHub organization changes later.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QCoreApplication, QDir, QStandardPaths

from runtime.app_version import APP_VERSION


DISPLAY_NAME = "ClipLM"
APPLICATION_ID = "org.cliplm.ClipLM"
ORGANIZATION_NAME = "cliplm"
ORGANIZATION_DOMAIN = "cliplm.org"

logger = logging.getLogger(__name__)


class AppPathMigrationError(RuntimeError):
    """Raised when choosing either storage directory could hide user data."""


@dataclass(frozen=True)
class AppPaths:
    """Filesystem locations owned by one ClipLM installation.

    Path objects are retained internally for safe path composition; strings are
    exposed only where existing Qt widgets and integration scripts expect them.
    """

    config: Path
    data: Path
    cache: Path

    def as_strings(self) -> tuple[str, str, str]:
        return str(self.config), str(self.data), str(self.cache)


def ensure_app_paths() -> AppPaths:
    """Resolve unique paths, migrate legacy directories, and create missing roots.

    Legacy paths are calculated using the exact Qt metadata and APIs used before
    the application ID was introduced. New paths use generic platform roots plus
    the explicit ID, making their final directory name predictable on every OS.
    """
    legacy_paths = _legacy_app_paths()
    _set_current_application_metadata()
    paths = _current_app_paths()

    migrate_legacy_paths(legacy_paths, paths)
    for path in (paths.config, paths.data, paths.cache):
        QDir().mkpath(str(path))
    return paths


def migrate_legacy_paths(legacy: AppPaths, current: AppPaths) -> None:
    """Move complete legacy directories without overwriting current storage.

    Renaming the whole directory keeps SQLite databases, sidecar files, prompts,
    thumbnails, and settings together. If both locations contain files, neither
    is modified because automatically combining two SQLite-backed app states is
    unsafe and could silently discard clipboard history.
    """
    migrations = []
    destinations = {}
    for category in ("config", "data", "cache"):
        source = getattr(legacy, category)
        destination = getattr(current, category)
        if _path_key(source) == _path_key(destination) or not source.exists():
            continue

        # Two categories sharing one destination is unsafe. This happened on
        # Windows when generic config and data roots were both %LOCALAPPDATA%.
        destination_key = _path_key(destination)
        if destination_key in destinations:
            other_category = destinations[destination_key]
            raise AppPathMigrationError(
                "ClipLM cannot migrate because the "
                f"{other_category} and {category} directories resolve to the "
                f"same destination: '{destination}'. Nothing was changed."
            )
        destinations[destination_key] = category

        # Validate every destination before moving the first directory. This
        # prevents a later conflict from producing a mixed old/new app state.
        if destination.exists() and any(destination.iterdir()):
            raise AppPathMigrationError(
                "ClipLM found data in both its old and new "
                f"{category} directories. Nothing was changed. Resolve the "
                f"conflict between '{source}' and '{destination}' before "
                "starting ClipLM again."
            )
        migrations.append((category, source, destination))

    for category, source, destination in migrations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            _move_to_empty_destination(source, destination)
        except OSError as error:
            raise AppPathMigrationError(
                f"ClipLM could not migrate {category} data from '{source}' "
                f"to '{destination}'. No destination data was overwritten."
            ) from error

        logger.info("Migrated ClipLM %s directory to %s", category, destination)


def _move_to_empty_destination(source: Path, destination: Path) -> None:
    """Move a directory without asking Windows to remove the destination first.

    Windows cannot replace an existing directory as consistently as POSIX. An
    empty target is temporarily renamed, then restored if moving the source fails.
    """
    empty_placeholder = None
    if destination.exists():
        empty_placeholder = destination.with_name(
            f".{destination.name}.empty-{uuid4().hex}"
        )
        destination.replace(empty_placeholder)

        # Recheck after the rename in case something populated the directory
        # between migration preflight and this operation.
        if any(empty_placeholder.iterdir()):
            empty_placeholder.replace(destination)
            raise OSError(f"Migration destination is not empty: {destination}")

    try:
        source.replace(destination)
    except OSError:
        if empty_placeholder is not None and not destination.exists():
            empty_placeholder.replace(destination)
        raise

    if empty_placeholder is not None:
        empty_placeholder.rmdir()


def _legacy_app_paths() -> AppPaths:
    """Reproduce the pre-application-ID path calculation exactly."""
    QCoreApplication.setOrganizationName(DISPLAY_NAME)
    QCoreApplication.setOrganizationDomain("")
    QCoreApplication.setApplicationName(DISPLAY_NAME)
    return AppPaths(
        config=Path(QStandardPaths.writableLocation(QStandardPaths.ConfigLocation))
        / DISPLAY_NAME,
        data=Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)),
        cache=Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)),
    )


def _set_current_application_metadata() -> None:
    """Set user-facing metadata separately from the immutable storage ID."""
    QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
    QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)
    QCoreApplication.setApplicationName(DISPLAY_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)


def _current_app_paths() -> AppPaths:
    """Build category paths from the generic roots selected by the OS."""
    return _app_paths_from_roots(
        Path(QStandardPaths.writableLocation(QStandardPaths.GenericConfigLocation)),
        Path(QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation)),
        Path(QStandardPaths.writableLocation(QStandardPaths.GenericCacheLocation)),
    )


def _app_paths_from_roots(
    config_root: Path,
    data_root: Path,
    cache_root: Path,
) -> AppPaths:
    """Keep category paths distinct when an OS maps them to the same root.

    On Windows, generic config and data locations commonly share %LOCALAPPDATA%.
    Only colliding categories receive a suffix, so Linux and macOS retain their
    existing shorter paths when their platform roots are already distinct.
    """
    roots = {
        "config": Path(config_root),
        "data": Path(data_root),
        "cache": Path(cache_root),
    }
    root_counts = {}
    for root in roots.values():
        key = _path_key(root)
        root_counts[key] = root_counts.get(key, 0) + 1

    resolved = {}
    for category, root in roots.items():
        path = root / APPLICATION_ID
        if root_counts[_path_key(root)] > 1:
            path /= category
        resolved[category] = path
    return AppPaths(**resolved)


def _path_key(path: Path) -> str:
    """Return a normalized key suitable for same-location comparisons."""
    return os.path.normcase(os.path.abspath(path))
