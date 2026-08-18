from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton


class SidebarTabButton(QToolButton):
    def __init__(self, text: str, icon: QIcon, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar_tab_button")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 46)
        self.setText(text)
        self.setIcon(icon)
        self.setIconSize(QSize(18, 18))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
