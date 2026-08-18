"""Coordination layer for update networking, persistence, and presentation.

UpdateService owns HTTP and manifest parsing, while UpdateDialog only renders
state. This QObject translates signals between them and persists successful
checks, keeping those responsibilities outside App.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import os

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from runtime.app_version import APP_VERSION
from services.update_service import (
    DOWNLOAD_PAGE_URL,
    UpdateResult,
    UpdateService,
    cached_update_result,
    current_platform_target,
    is_update_check_due,
    parse_update_manifest,
)
from ui.dialogs.update import UpdateDialog

from .settings_controller import SettingsController


class UpdateCoordinator(QObject):
    """Coordinate update state across networking, persistence, and update UI."""

    def __init__(
        self,
        tabs,
        settings: SettingsController,
        parent=None,
    ):
        super().__init__(parent)
        self.tabs = tabs
        self.settings = settings
        self.service = UpdateService(APP_VERSION, self)
        self.dialog = UpdateDialog(APP_VERSION, parent)
        self.last_result = cached_update_result(
            APP_VERSION,
            settings.settings.get("updates", {}),
        )
        self._debug_enabled = False
        self._connect_signals()
        self._restore_cached_state()
        self._debug_enabled = self._apply_debug_state()
        QTimer.singleShot(3_000, self.check_automatically)

    def _connect_signals(self) -> None:
        self.tabs.updateRequested.connect(self.show_dialog)
        self.dialog.checkRequested.connect(self.service.check)
        self.dialog.downloadRequested.connect(self.open_download_page)
        self.service.checkingStarted.connect(self.dialog.set_checking)
        self.service.checkSucceeded.connect(self._handle_success)
        self.service.checkFailed.connect(self.dialog.set_error)

    def _restore_cached_state(self) -> None:
        # Cached metadata gives immediate feedback; a scheduled network check
        # refreshes it later only after the configured interval.
        if self.last_result is None:
            return
        self.dialog.set_result(self.last_result)
        self.tabs.set_update_available(
            self.last_result.available,
            self.last_result.latest_version,
        )

    def show_dialog(self) -> None:
        if self.service.is_checking:
            self.dialog.set_checking()
        elif self.service.last_error:
            self.dialog.set_error(self.service.last_error)
        elif self.last_result is not None:
            self.dialog.set_result(self.last_result)
        else:
            self.dialog.set_idle()

        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

        if (
            self.last_result is None
            and not self.service.is_checking
            and not self.service.last_error
        ):
            self.service.check()

    def check_automatically(self) -> None:
        if self._debug_enabled:
            return
        update_settings = self.settings.settings.get("updates", {})
        if not update_settings.get("check_automatically", True):
            return
        if is_update_check_due(update_settings.get("last_checked_at", "")):
            self.service.check()

    def _handle_success(self, result: UpdateResult) -> None:
        # Persist release metadata only. Clipboard and account data are not part
        # of the manifest request or this settings update.
        self.last_result = result
        self.dialog.set_result(result)
        self.tabs.set_update_available(result.available, result.latest_version)
        checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.settings.update(
            {
                "updates": {
                    "last_checked_at": checked_at.replace("+00:00", "Z"),
                    "last_known_version": result.latest_version,
                    "last_target": result.target,
                    "last_generated_at": result.generated_at,
                    "last_summary": result.summary,
                    "last_available_packages": list(result.available_packages),
                }
            }
        )

    @staticmethod
    def open_download_page() -> None:
        QDesktopServices.openUrl(QUrl(DOWNLOAD_PAGE_URL))

    def _apply_debug_state(self) -> bool:
        version = os.environ.get("CLIPLM_DEBUG_UPDATE_VERSION", "").strip()
        if not version:
            return False

        try:
            target = current_platform_target()
            result = parse_update_manifest(
                {
                    "schema_version": 1,
                    "product": "cliplm",
                    "channel": "stable",
                    "generated_at": "development preview",
                    "summary": "Development preview of the ClipLM update dialog.",
                    "targets": {
                        target: {
                            "recommended_version": version,
                            "packages": {},
                        }
                    },
                },
                APP_VERSION,
                target,
            )
        except Exception as error:
            logging.getLogger(__name__).warning("Invalid debug update: %s", error)
            return False

        self.last_result = result
        self.dialog.set_result(result)
        self.tabs.set_update_available(result.available, result.latest_version)
        return True
