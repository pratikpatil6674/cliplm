"""Platform-specific filesystem locations and legacy-directory migration.

Storage uses an immutable application identifier rather than the display name.
This prevents another application named ClipLM from sharing our settings or
database directories. The identifier remains stable even if the project website
or GitHub organization changes later.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

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
    paths = AppPaths(
        config=_generic_location(QStandardPaths.GenericConfigLocation),
        data=_generic_location(QStandardPaths.GenericDataLocation),
        cache=_generic_location(QStandardPaths.GenericCacheLocation),
    )

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
    for category in ("config", "data", "cache"):
        source = getattr(legacy, category)
        destination = getattr(current, category)
        if source == destination or not source.exists():
            continue

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
        if destination.exists():
            destination.rmdir()

        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            source.replace(destination)
        except OSError as error:
            raise AppPathMigrationError(
                f"ClipLM could not migrate {category} data from '{source}' "
                f"to '{destination}'. The original data was left in place."
            ) from error

        logger.info("Migrated ClipLM %s directory to %s", category, destination)


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


def _generic_location(location: QStandardPaths.StandardLocation) -> Path:
    """Append the immutable app ID to an OS-selected generic root."""
    return Path(QStandardPaths.writableLocation(location)) / APPLICATION_ID
