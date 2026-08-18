import os
import shutil
import subprocess
import sys
from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QObject, QMimeData

try:
    from pynput.keyboard import Key, Controller
except Exception:
    Key = None
    Controller = None


class ClipboardService(QObject):
    clipboardChanged = Signal(QMimeData)

    def __init__(self, app):
        print("clipboard service init")
        super().__init__()
        self.app = app
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self.internal_copy = False
        self.keyboard = Controller() if self._should_use_pynput() and Controller else None

    def simulate_paste_event_with_pynput(self):
        """Simulate a global paste action using pynput."""
        if self.keyboard is None or Key is None:
            return

        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.press("v")
            self.keyboard.release("v")

    def simulate_paste_event_with_ydotool(self):
        """Use ydotool on Wayland to send Ctrl+V."""
        ydotool_path = self._find_executable_path("ydotool")
        if not ydotool_path:
            print("ydotool paste failed: ydotool executable was not found", file=sys.stderr)
            return

        try:
            subprocess.run(
                [ydotool_path, "key", "--key-delay", "0", "CTRL+v"],
                check=False,
            )
        except Exception as exc:
            print(f"ydotool paste failed: {exc}", file=sys.stderr)

    def simulate_paste_event(self):
        if self._is_wayland():
            self.simulate_paste_event_with_ydotool()
        else:
            self.simulate_paste_event_with_pynput()

    def _is_wayland(self):
        if sys.platform != "linux":
            return False
        session_type = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
        return session_type == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))

    def _should_use_pynput(self):
        return sys.platform in ("darwin", "win32") or (
            sys.platform == "linux" and not self._is_wayland()
        )

    def _find_executable_path(self, command_name: str) -> str | None:
        """Resolve a binary from the current runtime PATH."""
        return shutil.which(command_name)

    def set_clipboard(self, qmime_data: QMimeData, trigger_paste: bool = True):
        self.internal_copy = True
        print("internal paste request, internal copy = ", self.internal_copy)
        self.clipboard.setMimeData(qmime_data)

        if trigger_paste:
            QTimer.singleShot(100, self.app.hide)
            QTimer.singleShot(200, self.simulate_paste_event)
            QTimer.singleShot(400, self.app.show)

    def on_clipboard_change(self):
        if self.internal_copy:
            self.internal_copy = False
            return
        self.clipboardChanged.emit(self.clipboard.mimeData())
