from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton


class SidebarTabButton(QToolButton):
    def __init__(self, text: str, icon: QIcon, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(50, 50)
        self.setText(text)
        self.setIcon(icon)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # Let Qt render the icon and label, keeping the button styling in CSS.
        self.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #5f6c80;
                border: none;
                border-radius: 10px;
                padding: 5px 5px 5px 5px;
                text-align: center;
                font-size: 7pt;
                font-weight: 500;
            }
            QToolButton:hover {
                background: rgba(93, 129, 197, 0.08);
            }
            QToolButton:checked {
                color: #FFFFFF;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                font-weight: 600;
            }
        """)
