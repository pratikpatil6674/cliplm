"""Platform-specific filesystem location resolution.

Qt determines suitable config, data, and cache roots for each operating system.
Keeping that policy here ensures database, settings, logs, and prompts do not
independently invent paths. App retains a thin overridable method so isolated
tests can redirect all writes to temporary directories.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QDir, QStandardPaths

from runtime.app_version import APP_VERSION


APP_NAME = "ClipLM"


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
    """Resolve platform-specific locations and create them before use.

    Organization/application metadata must be set before asking QStandardPaths
    for AppDataLocation because it participates in the generated directory.
    """
    QCoreApplication.setOrganizationName(APP_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)

    paths = AppPaths(
        config=Path(QStandardPaths.writableLocation(QStandardPaths.ConfigLocation))
        / APP_NAME,
        data=Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)),
        cache=Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation)),
    )
    for path in (paths.config, paths.data, paths.cache):
        QDir().mkpath(str(path))
    return paths
