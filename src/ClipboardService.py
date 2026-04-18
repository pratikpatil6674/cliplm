# import pyperclip
# import pyautogui
import sys
from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QObject, QMimeData
from pynput.keyboard import Key, Controller
class ClipboardService(QObject):
    
    clipboardChanged = Signal(QMimeData)
    def __init__(self, app):
        print("clipboard service init")
        super().__init__()
        self.app = app
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self.internal_copy = False
        self.keyboard = Controller()
    
    # def simulate_paste_event(self):
    #     """Simulate a global paste action using pyautogui. This is cross platform."""

    #     if sys.platform == 'darwin':
    #         pyautogui.hotkey('command', 'v')
    #     else:
    #         pyautogui.hotkey('ctrl', 'v')
    
    def simulate_paste_event(self):
        """ Simulate a global paste action using pynput. This is cross platform."""
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press('v')
            self.keyboard.release('v')
      
    def set_clipboard(self, qmime_data : QMimeData, trigger_paste: bool = True):
        self.internal_copy = True
        print("internal paste request, internal copy = ", self.internal_copy)
        self.clipboard.setMimeData(qmime_data)
        
        if trigger_paste:
            QTimer.singleShot(1, self.app.hide)
            QTimer.singleShot(100, self.simulate_paste_event)
            QTimer.singleShot(100, self.app.show)
    

    def on_clipboard_change(self):
        if self.internal_copy:
            self.internal_copy = False
            return
        self.clipboardChanged.emit(self.clipboard.mimeData())