"""Main window and composition root for the desktop application.

The window owns application lifecycle concerns: creating top-level
collaborators, exposing established integration attributes, positioning the
window, and handling shutdown. Feature construction belongs to adjacent
composer/controller modules so one feature cannot continuously grow App.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QTabWidget, QVBoxLayout, QWidget

from core.clip_data import ClipData
from runtime.app_paths import ensure_app_paths
from runtime.logging_setup import configure_app_logger
from ui.resources import APP_ICON

from .bootstrap import build_application_services
from .settings_controller import SettingsController
from .tab_composer import TabComposer, TabComposition
from .tray_controller import TrayController
from .update_coordinator import UpdateCoordinator


logger = logging.getLogger(__name__)


class App(QWidget):
    """ClipLM's main window and application-level composition root.

    This is where concrete implementations are selected and connected. Lower
    layers receive collaborators instead of constructing global services, which
    keeps dependencies explicit and replaceable in tests.
    """

    def __init__(self):
        super().__init__()
        self.config_dir, self.data_dir, self.cache_dir = self.ensure_app_dirs()
        # Settings are loaded first because the active LLM profile selects the
        # AI client, while appearance and translation settings define initial
        # runtime and UI state.
        self.settings_controller = SettingsController(self.data_dir)
        self.settings_store = self.settings_controller.store
        self.settings_controller.apply_appearance()

        services = build_application_services(
            self, self.config_dir, self.data_dir, self.settings
        )
        self.clipboard_service = services.clipboard
        self.ai_service = services.ai
        self.translate_service = services.translate
        self.clipboard_store = services.clips
        self.prompts_store = services.prompts

        self._setup_ui(services)
        self.settings_controller.apply_appearance(self.tabs)
        self.settings_controller.apply_translate_visibility(
            self.tabs, self.translate_tab, self.clipboard_tab
        )

        self.update_coordinator = UpdateCoordinator(
            self.tabs, self.settings_controller, self
        )
        self.update_service = self.update_coordinator.service
        self.update_dialog = self.update_coordinator.dialog

        self.setup_tray_icon()
        configure_app_logger(str(Path(self.data_dir) / "cliplm.log"))
        logger.info("App initialized successfully")

    @property
    def settings(self):
        """Expose current settings without retaining a stale dictionary."""
        return self.settings_controller.settings

    def _setup_ui(self, services) -> None:
        self.setObjectName("app_window")
        self.setWindowTitle("ClipLM")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.window_radius = 12

        composition = TabComposer(
            self,
            services,
            self.settings,
            self.config_dir,
            self.data_dir,
            self.cache_dir,
        ).compose(
            show_window=self.move_near_cursor,
            save_settings=self._save_settings,
            save_languages=self._handle_translate_language_change,
        )
        self._install_tab_composition(composition)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
        self.tabs.setTabPosition(QTabWidget.West)
        self.move_near_cursor()

    def _install_tab_composition(self, composition: TabComposition) -> None:
        """Expose established App attributes while construction lives elsewhere."""
        self.tabs = composition.tabs
        self.clipboard_model = composition.clipboard_model
        self.clipboard_tab = composition.clipboard_tab
        self.clipboard_presenter = composition.clipboard_presenter
        self.favorites_model = composition.favorites_model
        self.favorites_tab = composition.favorites_tab
        self.favorites_presenter = composition.favorites_presenter
        self.manual_model = composition.manual_model
        self.manual_tab = composition.manual_tab
        self.manual_presenter = composition.manual_presenter
        self.translate_tab = composition.translate_tab
        self.translate_presenter = composition.translate_presenter
        self.ai_tab = composition.ai_tab
        self.ai_presenter = composition.ai_presenter
        self.settings_tab = composition.settings_tab
        self.tab_shortcuts = composition.tab_shortcuts

    def ensure_app_dirs(self) -> tuple[str, str, str]:
        """Compatibility hook used by isolated screenshot and test subclasses."""
        paths = ensure_app_paths()
        print(f"Config: {paths.config}, Data: {paths.data}, Cache: {paths.cache}")
        return paths.as_strings()

    def _save_settings(self) -> None:
        # Persist first, then reconfigure long-lived service QObjects in place;
        # replacing them would invalidate presenter signal connections.
        self.settings_controller.save_from_views(
            self.settings_tab, self.translate_tab
        )
        self.settings_controller.apply_appearance(self.tabs)
        self.settings_controller.configure_ai(self.ai_service, self.ai_presenter)
        self.settings_controller.configure_translation(
            self.translate_service, self.translate_tab
        )
        self.settings_controller.apply_translate_visibility(
            self.tabs, self.translate_tab, self.clipboard_tab
        )

    def _handle_translate_language_change(
        self, source_language: str, destination_language: str
    ) -> None:
        self.settings_controller.save_translate_languages(
            source_language, destination_language
        )

    def _handle_tab_change(self, index: int) -> None:
        current_widget = self.tabs.widget(index)
        mime_data = self.clipboard_service.clipboard.mimeData()
        clip_data = ClipData.from_qmime(mime_data) if mime_data else None

        if (
            current_widget is self.translate_tab
            and clip_data
            and clip_data.is_text_like()
        ):
            self.translate_presenter.update_input_text(clip_data.data)

        is_ai_tab = current_widget is self.ai_tab
        self.ai_tab.set_ai_enabled(is_ai_tab)
        if is_ai_tab and clip_data:
            self.ai_presenter.update_clipdata_preview(clip_data)

    def center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        geometry = self.geometry()
        self.move(
            (available.width() - geometry.width()) // 2,
            (available.height() - geometry.height()) // 2,
        )

    def move_near_cursor(
        self, offset_x: int = 16, offset_y: int = 16, tab_index: int = 0
    ) -> None:
        QTimer.singleShot(100, self.show_window)
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        if screen is None:
            self.center_on_screen()
            return

        available = screen.availableGeometry()
        geometry = self.frameGeometry()
        width = geometry.width() or self.width()
        height = geometry.height() or self.height()
        max_x = available.right() - width + 1
        max_y = available.bottom() - height + 1
        self.move(
            max(available.left(), min(cursor_pos.x() + offset_x, max_x)),
            max(available.top(), min(cursor_pos.y() + offset_y, max_y)),
        )
        self.tabs.setCurrentIndex(tab_index)

    def setup_tray_icon(self) -> None:
        """Compatibility hook that delegates desktop integration to its owner."""
        self.tray_controller = TrayController(self, APP_ICON)
        self.tray_icon = self.tray_controller.icon
        self.show_action = self.tray_controller.show_action
        self.hide_action = self.tray_controller.hide_action
        self.quit_action = self.tray_controller.quit_action

    def show_window(self) -> None:
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
