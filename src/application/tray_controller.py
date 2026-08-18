"""Desktop tray integration kept separate from the main window layout.

Tray availability varies across desktop environments. Isolating this adapter
lets screenshot and CI subclasses skip it without replacing App or introducing
desktop-specific branches throughout the window.
"""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayController(QObject):
    """Own the system tray icon, menu actions, and activation behavior.

    The window is the Qt parent, matching QObject ownership and avoiding
    explicit destruction logic.
    """

    def __init__(self, window, icon: QIcon):
        super().__init__(window)
        self.window = window
        self.icon = QSystemTrayIcon(window)
        self.icon.setIcon(icon)
        self.icon.setToolTip("Clipboard Manager")

        self.show_action = QAction("Show", window)
        self.hide_action = QAction("Hide", window)
        self.quit_action = QAction("Quit", window)
        self.show_action.triggered.connect(window.show_window)
        self.hide_action.triggered.connect(window.hide)
        self.quit_action.triggered.connect(QApplication.quit)

        menu = QMenu()
        menu.addAction(self.show_action)
        menu.addAction(self.hide_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        self.icon.setContextMenu(menu)
        self.icon.activated.connect(self._handle_activation)
        self.icon.show()

    def _handle_activation(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.window.show_window()
