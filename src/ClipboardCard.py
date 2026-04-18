
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QListWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QListWidgetItem,
    QDialog,
    QCheckBox,
    QFrame,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, QMimeData
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QSizePolicy
from resources import *
from ClipData import ClipData

class ClipboardCard(QFrame):
    copyRequested = Signal(str)
    pasteRequested = Signal(str)
    deleteRequested = Signal(str)
    favRequested = Signal(str)
    MAX_CARD_HEIGHT = 180
    def __init__(self, id: str, clip_data: ClipData):
        super().__init__()
        self.id = id
        self.clip_data = clip_data
        
        self._setup_ui()
        self._setup_styles()
        self._connect_signals()
        
    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(min(hint.height(), self.MAX_CARD_HEIGHT))
        return hint

    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(60)
        self.setMaximumHeight(self.MAX_CARD_HEIGHT)
        # list_item_widget = QWidget()
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        # outer_layout.setAlignment(Qt.AlignTop)  # Align content to the top
        # layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout = QVBoxLayout()
        buttons_layout.addStretch()
        # inner_layout.setAlignment(Qt.AlignTop)  # Align content to the top
        # inner_layout.setContentsMargins(0, 0, 0, 0)
        # inner_layout.setSpacing(0)
        
        button_size = 15
        self.fav_button = QPushButton()
        self.fav_button.setIcon(STAR_ICON)
        self.fav_button.setCheckable(True)
        self.fav_button.setFixedSize(button_size, button_size)
        buttons_layout.addWidget(self.fav_button)
        buttons_layout.addStretch()

        self.copy_button = QPushButton()
        self.copy_button.setIcon(COPY_ICON_LIGHT)
        self.copy_button.setFixedSize(button_size, button_size)
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # self.text_field = QLabel(self.text)
        # self.text_field.setWordWrap(True)
        # self.text_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.text_field.setMaximumHeight(self.MAX_CARD_HEIGHT - 30)  # allow padding

        self.clip_widget = self.clip_data.create_preview_widget(max_height=self.MAX_CARD_HEIGHT - 30)
        layout.addWidget(self.clip_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

    def _setup_styles(self): 
        # for button in [self.fav_button, self.copy_button]:
        #     button.setStyleSheet("""
        #         QPushButton {
        #             max-width: 20px; 
        #             max-height: 20px; 
        #             padding: 0px; 
        #             border: none; 
        #             background-color: transparent;
        #         }
        #         QPushButton:hover {
        #             background-color: #3399ff;
        #         }
        #     """)
        
        # self.text_field.setStyleSheet(f"color: black; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 0px; background-color: transparent;")

        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                background-color: #ffffff;
                border-radius: 10px;
                padding: 5px;
                padding-bottom: 10px;
            }
            QFrame:hover {
                border: 2px solid #2979ff;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLabel {
                border: none;
                color: black;
                font-size: 10pt; 
                padding: 0px; 
                margin: 0px; 
                background-color: transparent;
            }
            QLabel:hover {
                border: none;
            }
        """)
    
    def _connect_signals(self):
        self.copy_button.clicked.connect(lambda : self.copy_item())
        self.fav_button.clicked.connect(lambda checked, id=self.id: self.toggle_favorite(id))
        self.clip_widget.mousePressEvent = lambda event: self.paste_item(event)

    def copy_item(self):
        self.copyRequested.emit(self.clip_data.database_id)
    
    def toggle_favorite(self, id):
        self.favRequested.emit(id)

    def paste_item(self, event):
        if event.button() == Qt.LeftButton:
            self.pasteRequested.emit(self.clip_data.database_id)