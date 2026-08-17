from pathlib import Path
from datetime import datetime, timezone
import logging
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton, QLabel,
    QHBoxLayout, QTextEdit, QListWidgetItem, QDialog, QCheckBox, QScrollArea
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect

from PySide6.QtGui import QCursor
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence, QShortcut, QColor, QMouseEvent, QAction
from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QCoreApplication, QStandardPaths, QDir, QSaveFile, QByteArray, QUrl
import asyncio
from googletrans import Translator
from ManualCard import ManualCard
from pathlib import Path
from resources import *
from ClipboardService import ClipboardService
from ClipData import ClipData
from TranslateService import TranslateService
from database import ClipboardStore

from ClipboardTab import ClipboardTab
from ClipboardPresenter import ClipboardPresenter


from FavoritesTab import FavoritesTab
from FavoritesPresenter import FavoritesPresenter
from ManualTab import ManualTab
from ManualPresenter import ManualPresenter
from TranslateTab import TranslateTab
from TranslatePresenter import TranslatePresenter
from AIPromptSidebarTab import AIPromptSidebarTab
from AIPresenter import AIPresenter
from PromptsStore import PromptsStore
from AIService import LLMService
from AppVersion import APP_VERSION
from UpdateDialog import UpdateDialog
from UpdateService import (
    DOWNLOAD_PAGE_URL,
    UpdateService,
    UpdateResult,
    cached_update_result,
    current_platform_target,
    is_update_check_due,
    parse_update_manifest,
)
from LoggingSetup import configure_app_logger
from LLMProfiles import active_profile, normalize_ai_settings
from SettingsStore import SettingsStore
from SettingsTab import SettingsTab
from SidebarTabWidget import SidebarTabWidget
from TabShortcuts import TabShortcuts
from ThemeManager import apply_app_theme


class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.config_dir, self.data_dir, self.cache_dir = self.ensure_app_dirs()
        self.settings_store = SettingsStore(
            Path(self.data_dir) / "settings.json",
            defaults={
                "appearance": {
                    "theme": "blue",
                    "dark_mode": False,
                },
                "ai": {
                    "active_profile_id": "",
                    "profiles": [],
                },
                "translate": {
                    "enabled": True,
                    "source_language": "auto",
                    "destination_language": "en",
                    "api": "google",
                },
                "updates": {
                    "check_automatically": True,
                    "channel": "stable",
                    "last_checked_at": "",
                    "last_known_version": "",
                    "last_target": "",
                    "last_generated_at": "",
                    "last_summary": "",
                    "last_available_packages": [],
                },
            },
        )
        self.settings = self.settings_store.get()
        normalized_ai_settings = normalize_ai_settings(
            self.settings.get("ai", {})
        )
        if normalized_ai_settings != self.settings.get("ai", {}):
            self.settings["ai"] = normalized_ai_settings
            self.settings_store.save(self.settings)
        self._apply_appearance_settings()
        self.clipboard_service = ClipboardService(self)
        selected_profile = active_profile(self.settings.get("ai", {})) or {}
        self.ai_service = LLMService(
            endpoint=selected_profile.get("endpoint", ""),
            api_key=selected_profile.get("api_key", ""),
            model=selected_profile.get("model", ""),
            profile_name=selected_profile.get("name", ""),
        )
        self.translate_service = TranslateService(self.ai_service)
        translate_settings = self.settings.get("translate", {})
        self.translate_service.configure(
            provider=translate_settings.get("api", "google"),
            llm_service=self.ai_service,
        )
        self.clipboard_store = ClipboardStore(Path(self.data_dir) / "clipboard.db", self.data_dir)
        self.prompts_store = PromptsStore(Path(self.config_dir) / "prompts.toml")
        self._setup_ui()
        self._apply_appearance_settings()
        self._setup_updates()

        self.setup_tray_icon()

        log_file = Path(self.data_dir) / "cliplm.log"
        configure_app_logger(str(log_file))
        logger = logging.getLogger(__name__)
        logger.info("App initialized successfully")

    
    def _setup_ui(self):
        self.setObjectName("app_window")
        self.setWindowTitle("ClipLM")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.window_radius = 12
        
        # Tab Layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = SidebarTabWidget()
        # self.tabs.currentChanged.connect(self._handle_tab_change)

        self.clipboard_model = self.clipboard_store.clipboard
        self.clipboard_tab = ClipboardTab()
        self.clipboard_presenter = ClipboardPresenter(
            self.clipboard_service,
            self.clipboard_model,
            self.clipboard_tab,
            self.move_near_cursor
        )
        self.clipboard_tab.presenter = self.clipboard_presenter
        self.tabs.addTab(self.clipboard_tab, "Clipboard")


        self.favorites_model = self.clipboard_store.favourites
        self.favorites_tab = FavoritesTab()
        self.favorites_presenter = FavoritesPresenter(
            self.clipboard_service,
            self.favorites_model,
            self.favorites_tab
        )
        self.favorites_tab.presenter = self.favorites_presenter
        self.clipboard_tab.favorites_presenter = self.favorites_presenter
        self.tabs.addTab(self.favorites_tab, "Favorites")

        self.manual_model = self.clipboard_store.notes
        self.manual_tab = ManualTab()
        self.manual_presenter = ManualPresenter(
            self.clipboard_service,
            self.manual_model,
            self.manual_tab
        )
        self.manual_tab.presenter = self.manual_presenter
        self.tabs.addTab(self.manual_tab, "Notes")
        
        self.translate_tab = TranslateTab()
        self.translate_presenter = TranslatePresenter(
            self.translate_service,
            self.translate_tab
        )
        self.translate_tab.presenter = self.translate_presenter
        translate_settings = self.settings.get("translate", {})
        self.translate_tab.set_translation_provider(
            translate_settings.get("api", "google")
        )
        self.translate_tab.set_selected_languages(
            translate_settings.get("source_language", "auto"),
            translate_settings.get("destination_language", "en"),
        )
        self.translate_tab.languageSettingsChanged.connect(self._handle_translate_language_change)
        self.clipboard_presenter.translate_presenter = self.translate_presenter
        self.tabs.addTab(self.translate_tab, "Translate")
        
        self.clipboard_presenter.refresh_view()
        self.favorites_presenter.refresh_view()
        self.manual_presenter.refresh_view()
        # Add tabs to main layout

        self.ai_tab = AIPromptSidebarTab(
            self.prompts_store,
            self.clipboard_service,
        )
        self.ai_presenter = AIPresenter(self.ai_service, self.ai_tab)
        self.ai_tab.promptExecutionRequested.connect(self.ai_presenter.execute_selected_prompt)
        self.clipboard_presenter.ai_presenter = self.ai_presenter
        self.tabs.addTab(self.ai_tab, "AI")

        self.settings_tab = SettingsTab(
            self.config_dir,
            self.data_dir,
            self.cache_dir,
        )
        self.settings_tab.set_settings(self.settings)
        self.settings_tab.saveRequested.connect(self._save_settings)
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tab_shortcuts = TabShortcuts(self, self.tabs)
        
        self.layout.addWidget(self.tabs)
        self.tabs.setTabPosition(QTabWidget.West)

        self.setLayout(self.layout)
        self.move_near_cursor()
        self._apply_translate_tab_visibility(
            self.settings.get("translate", {}).get("enabled", True)
        )
        # self._handle_tab_change(self.tabs.currentIndex())
        # self.translate_presenter.translate_text("Hello")

    def _setup_updates(self) -> None:
        self.update_service = UpdateService(APP_VERSION, self)
        self.update_dialog = UpdateDialog(APP_VERSION, self)
        self._last_update_result = cached_update_result(
            APP_VERSION,
            self.settings.get("updates", {}),
        )
        self._debug_update_enabled = False

        self.tabs.updateRequested.connect(self._show_updates_dialog)
        self.update_dialog.checkRequested.connect(self.update_service.check)
        self.update_dialog.downloadRequested.connect(self._open_download_page)
        self.update_service.checkingStarted.connect(self.update_dialog.set_checking)
        self.update_service.checkSucceeded.connect(self._handle_update_success)
        self.update_service.checkFailed.connect(self._handle_update_failure)

        if self._last_update_result is not None:
            self.update_dialog.set_result(self._last_update_result)
            self.tabs.set_update_available(
                self._last_update_result.available,
                self._last_update_result.latest_version,
            )

        self._debug_update_enabled = self._apply_debug_update_state()
        QTimer.singleShot(3_000, self._check_updates_automatically)

    def _show_updates_dialog(self) -> None:
        if self.update_service.is_checking:
            self.update_dialog.set_checking()
        elif self.update_service.last_error:
            self.update_dialog.set_error(self.update_service.last_error)
        elif self._last_update_result is not None:
            self.update_dialog.set_result(self._last_update_result)
        else:
            self.update_dialog.set_idle()

        self.update_dialog.show()
        self.update_dialog.raise_()
        self.update_dialog.activateWindow()

        if (
            self._last_update_result is None
            and not self.update_service.is_checking
            and not self.update_service.last_error
        ):
            self.update_service.check()

    def _check_updates_automatically(self) -> None:
        if self._debug_update_enabled:
            return
        update_settings = self.settings.get("updates", {})
        if not update_settings.get("check_automatically", True):
            return
        if is_update_check_due(update_settings.get("last_checked_at", "")):
            self.update_service.check()

    def _handle_update_success(self, result: UpdateResult) -> None:
        self._last_update_result = result
        self.update_dialog.set_result(result)
        self.tabs.set_update_available(
            result.available,
            result.latest_version,
        )
        checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        checked_at = checked_at.replace("+00:00", "Z")
        self.settings = self.settings_store.update(
            {
                "updates": {
                    "last_checked_at": checked_at,
                    "last_known_version": result.latest_version,
                    "last_target": result.target,
                    "last_generated_at": result.generated_at,
                    "last_summary": result.summary,
                    "last_available_packages": list(result.available_packages),
                }
            }
        )

    def _handle_update_failure(self, message: str) -> None:
        self.update_dialog.set_error(message)

    def _open_download_page(self) -> None:
        QDesktopServices.openUrl(QUrl(DOWNLOAD_PAGE_URL))

    def _apply_debug_update_state(self) -> bool:
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

        self._last_update_result = result
        self.update_dialog.set_result(result)
        self.tabs.set_update_available(
            result.available,
            result.latest_version,
        )
        return True

    def ensure_app_dirs(self):
        APP_NAME = "ClipLM"
        QCoreApplication.setOrganizationName(APP_NAME)
        QCoreApplication.setApplicationName(APP_NAME)

        QCoreApplication.setApplicationVersion(APP_VERSION)
        config_dir = QStandardPaths.writableLocation(QStandardPaths.ConfigLocation)
        config_dir = str(Path(config_dir) / APP_NAME)
        data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)

        QDir().mkpath(config_dir)
        QDir().mkpath(data_dir)
        QDir().mkpath(cache_dir)

        print(f"Config: {config_dir}, Data: {data_dir}, Cache: {cache_dir}")
        return config_dir, data_dir, cache_dir
    
    def center_on_screen(self):
        # Get the main screen's available geometry
        screen = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.geometry()
        
        # Calculate the new center point (x, y) to center the window on screen
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        
        self.move(x, y)

    def move_near_cursor(self, offset_x=16, offset_y=16, tab_index=0):
        QTimer.singleShot(100, self.show_window)
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()

        if screen is None:
            self.center_on_screen()
            return

        available_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_width = window_geometry.width() or self.width()
        window_height = window_geometry.height() or self.height()

        target_x = cursor_pos.x() + offset_x
        target_y = cursor_pos.y() + offset_y

        max_x = available_geometry.right() - window_width + 1
        max_y = available_geometry.bottom() - window_height + 1
        x = max(available_geometry.left(), min(target_x, max_x))
        y = max(available_geometry.top(), min(target_y, max_y))

        self.move(x, y)

        # self.tabs.setCurrentWidget(self.ai_tab)
        self.tabs.setCurrentIndex(tab_index)

    def _handle_tab_change(self, index):
        current_widget = self.tabs.widget(index)
        mime_data = self.clipboard_service.clipboard.mimeData()
        clip_data = ClipData.from_qmime(mime_data) if mime_data else None

        if current_widget is self.translate_tab and clip_data and clip_data.is_text_like():
            self.translate_presenter.update_input_text(clip_data.data)

        if hasattr(self.ai_tab, "set_ai_enabled"):
            is_ai_tab = current_widget is self.ai_tab
            self.ai_tab.set_ai_enabled(is_ai_tab)
            if is_ai_tab and clip_data:
                self.ai_presenter.update_clipdata_preview(clip_data)

    def _save_settings(self):
        updated_settings = self.settings_tab.get_settings()
        updated_settings["translate"]["source_language"] = self.translate_tab.get_source_language()
        updated_settings["translate"]["destination_language"] = self.translate_tab.get_destination_language()
        self.settings = self.settings_store.update(updated_settings)
        self.settings_tab.set_settings(self.settings)
        self._apply_appearance_settings()
        self._apply_ai_settings()
        self._apply_translate_settings()
        self._apply_translate_tab_visibility(
            self.settings.get("translate", {}).get("enabled", True)
        )

    def _apply_appearance_settings(self):
        appearance_settings = self.settings.get("appearance", {})
        app = QApplication.instance()
        if app is not None:
            apply_app_theme(
                app,
                theme_name=appearance_settings.get("theme", "blue"),
                dark_mode=appearance_settings.get("dark_mode", False),
            )
            if hasattr(self, "tabs"):
                self.tabs.set_dark_mode(
                    appearance_settings.get("dark_mode", False)
                )

    def _apply_ai_settings(self):
        selected_profile = active_profile(self.settings.get("ai", {})) or {}
        self.ai_service.configure(
            endpoint=selected_profile.get("endpoint", ""),
            api_key=selected_profile.get("api_key", ""),
            model=selected_profile.get("model", ""),
            profile_name=selected_profile.get("name", ""),
        )
        if hasattr(self, "ai_presenter"):
            self.ai_presenter.show_model_identity()

    def _apply_translate_settings(self):
        translate_settings = self.settings.get("translate", {})
        provider = translate_settings.get("api", "google")
        self.translate_service.configure(
            provider=provider,
            llm_service=self.ai_service,
        )
        self.translate_tab.set_translation_provider(provider)

    def _handle_translate_language_change(self, source_language, destination_language):
        self.settings = self.settings_store.update(
            {
                "translate": {
                    "source_language": source_language,
                    "destination_language": destination_language,
                }
            }
        )

    def _apply_translate_tab_visibility(self, enabled):
        translate_index = self.tabs.indexOf(self.translate_tab)
        if translate_index >= 0:
            self.tabs.setTabVisible(translate_index, enabled)
            if not enabled and self.tabs.currentWidget() is self.translate_tab:
                self.tabs.setCurrentWidget(self.clipboard_tab)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(APP_ICON)
        self.tray_icon.setToolTip("Clipboard Manager")

        tray_menu = QMenu()

        self.show_action = QAction("Show", self)
        self.hide_action = QAction("Hide", self)
        self.quit_action = QAction("Quit", self)

        self.show_action.triggered.connect(self.show_window)
        self.hide_action.triggered.connect(self.hide)
        self.quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def show_window(self):
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
