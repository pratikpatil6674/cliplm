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
        self.last_active_window = self.get_active_window()
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self.internal_copy = False
    
    def get_active_window(self):
        """Get the currently active window ID using xdotool."""
        try:
            return subprocess.check_output(["xdotool", "getactivewindow"]).strip().decode()
        except subprocess.CalledProcessError:
            return None

    def update_active_window(self):
        """Update the last active window dynamically."""
        current_window = self.get_active_window()
        if current_window and current_window != str(self.app.winId()):  # Ignore the clipboard manager itself
            self.last_active_window = current_window

    def focus_previous_window(self):
        """Refocus the previously active window before pasting."""
        if self.last_active_window:
            subprocess.run(["xdotool", "windowactivate", self.last_active_window])

    def simulate_paste_event(self):
        """Simulate a global paste action using xdotool."""
        # returncode=subprocess.run(["xdotool", "key", "ctrl+v"])
        # print("Return code:", returncode)

        import pyautogui
        pyautogui.hotkey('ctrl', 'v')

    def copy_text(self, text):
        if isinstance(text, str):
            pyperclip.copy(text)
            self.internal_copy = True
            
    def paste_text(self, item):
        # if isinstance(item, str):
        #     pyperclip.copy(item)
        # else:
        #     pyperclip.copy(item.text())
        self.internal_copy = True
        print("internal paste request, internal copy = ", self.internal_copy)
        self.clipboard.setMimeData(item)
        print("clipboard set to ", item.text())
        # QTimer.singleShot(10, lambda: QApplication.clipboard().setMimeData(item))
        # Ensure focus is restored to the last active window before pasting
        # QTimer.singleShot(100, self.focus_previous_window)
        QTimer.singleShot(10, self.app.hide)
        QTimer.singleShot(10, self.simulate_paste_event)
        QTimer.singleShot(100, self.app.show) 
    

    def on_clipboard_change(self):
        if self.internal_copy:
            self.internal_copy = False
            return
        print("clipboard changed mime data", id(self.clipboard.mimeData()))
        self.clipboardChanged.emit(self.clipboard.mimeData())