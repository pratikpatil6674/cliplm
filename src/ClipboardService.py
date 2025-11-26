import subprocess
import pyperclip
import time
from PySide6.QtCore import Qt, QTimer

from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QObject, QMimeData
class ClipboardService(QObject):
    
    clipboardChanged = Signal(QMimeData)
    def __init__(self, app):
        print("clipboard service init")
        super().__init__()
        self.app = app
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self.internal_copy = False
    
    def simulate_paste_event(self):
        """Simulate a global paste action using pyautogui."""

        import pyautogui
        pyautogui.hotkey('ctrl', 'v')

    def copy_text(self, text):
        if isinstance(text, str):
            pyperclip.copy(text)
            self.internal_copy = True
            
    def set_clipboard(self, qmime_data : QMimeData, trigger_paste: bool = True):
        self.internal_copy = True
        print("internal paste request, internal copy = ", self.internal_copy)
        self.clipboard.setMimeData(qmime_data)
        
        if trigger_paste:
            QTimer.singleShot(10, self.app.hide)
            QTimer.singleShot(10, self.simulate_paste_event)
            QTimer.singleShot(100, self.app.show) 
    

    def on_clipboard_change(self):
        if self.internal_copy:
            self.internal_copy = False
            return
        self.clipboardChanged.emit(self.clipboard.mimeData())