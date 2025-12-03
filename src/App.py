import sys
from pathlib import Path
import pyperclip
import subprocess
import json
import os
import time
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
from PySide6.QtGui import QIcon, QKeySequence, QShortcut, QColor, QMouseEvent
from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QCoreApplication, QStandardPaths, QDir, QSaveFile, QByteArray
import qt_material
import asyncio
from googletrans import Translator
from ManualCard import ManualCard
from pathlib import Path
from resources import *
from ClipboardService import ClipboardService
from TranslateService import GoogleTranslateService
from JsonDB import ClipboardDB, FavoritesDB, ManualDB
from SqlDB import ClipboardStore

from ClipboardTab import ClipboardTab
from ClipboardPresenter import ClipboardPresenter


from FavoritesTab import FavoritesTab
from FavoritesPresenter import FavoritesPresenter
from ManualTab import ManualTab
from ManualPresenter import ManualPresenter
from TranslateTab import TranslateTab
from TranslatePresenter import TranslatePresenter
from AITab import AITab
from AIPresenter import AIPresenter
from PromptsStore import PromptsStore
from AIService import LLMService
class App(QWidget):
    
    def __init__(self):
        super().__init__()
        self.clipboard_service = ClipboardService(self)
        self.translate_service = GoogleTranslateService()
        self.config_dir, self.data_dir, self.cache_dir = self.ensure_app_dirs()
        self.clipboard_store = ClipboardStore(Path(self.data_dir) / "clipboard.db", self.data_dir)

        self.ai_service = LLMService()
        self.prompts_store = PromptsStore(Path(self.config_dir) / "prompts.toml")
        self._setup_ui()
        self._set_styles()

    
    def _setup_ui(self):
        self.setWindowTitle("Clipboard Manager")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.window_radius = 12
        
        # Tab Layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()

        self.clipboard_model = self.clipboard_store.clipboard
        self.clipboard_tab = ClipboardTab()
        self.clipboard_presenter = ClipboardPresenter(self.clipboard_service, self.clipboard_model, self.clipboard_tab)
        self.clipboard_tab.presenter = self.clipboard_presenter
        self.tabs.addTab(self.clipboard_tab, "Clipboard")


        self.favorites_model = self.clipboard_store.favourites
        self.favorites_tab = FavoritesTab()
        self.favorites_presenter = FavoritesPresenter(self.clipboard_service, self.favorites_model, self.favorites_tab)
        self.favorites_tab.presenter = self.favorites_presenter
        self.clipboard_tab.favorites_presenter = self.favorites_presenter
        self.tabs.addTab(self.favorites_tab, "Favorites")

        self.manual_model = self.clipboard_store.notes
        self.manual_tab = ManualTab()
        self.manual_presenter = ManualPresenter(self.clipboard_service, self.manual_model, self.manual_tab)
        self.manual_tab.presenter = self.manual_presenter
        self.tabs.addTab(self.manual_tab, "Notes")
        
        self.translate_tab = TranslateTab()
        self.translate_presenter = TranslatePresenter(self.translate_service, self.translate_tab)
        self.translate_tab.presenter = self.translate_presenter
        self.clipboard_presenter.translate_presenter = self.translate_presenter
        self.tabs.addTab(self.translate_tab, "Translate")
        
        self.clipboard_presenter.refresh_view()
        self.favorites_presenter.refresh_view()
        self.manual_presenter.refresh_view()
        # Add tabs to main layout

        self.ai_tab = AITab(self.prompts_store)
        self.ai_presenter = AIPresenter(self.ai_service, self.ai_tab)
        self.clipboard_presenter.ai_presenter = self.ai_presenter
        self.tabs.addTab(self.ai_tab, "AI")
        
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)
        self.center_on_screen()
        # self.translate_presenter.translate_text("Hello")

    def _set_styles(self):
        self.setStyleSheet(f"background-color: #F9FBFD; ")
        qt_material.apply_stylesheet(self, theme='light_blue.xml')
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QTabBar::tab { 
                text-transform: none; 
                font-size: 15px; font-family: Ubuntu, sans-serif;
            }
        """)
    

    def ensure_app_dirs(self):
        APP_NAME = "NeuroClip"
        QCoreApplication.setOrganizationName(APP_NAME)
        QCoreApplication.setApplicationName(APP_NAME)

        config_dir = QStandardPaths.writableLocation(QStandardPaths.ConfigLocation)
        config_dir = f"{config_dir}/{APP_NAME}"
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