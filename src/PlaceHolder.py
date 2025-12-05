from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap, QImage

class Placeholder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._current = None   # currently displayed widget

    def clear(self):
        """Remove existing widget."""
        if self._current:
            self._layout.removeWidget(self._current)
            self._current.setParent(None)
            self._current = None

    def set_widget(self, widget: QWidget):
        """Set any QWidget (QLabel, custom widget, etc.)."""
        self.clear()
        self._current = widget
        self._layout.addWidget(widget)

    def set_qimage(self, qimg: QImage):
        """Display a QImage automatically as QLabel."""
        label = QLabel()
        pix = QPixmap.fromImage(qimg)
        label.setPixmap(pix)
        label.setScaledContents(True)
        self.set_widget(label)

    def set_text(self, text: str):
        """Display plain text."""
        label = QLabel(text)
        label.setWordWrap(True)
        self.set_widget(label)
