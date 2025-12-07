
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton, QLabel,
    QHBoxLayout, QTextEdit, QListWidgetItem, QDialog, QCheckBox, QScrollArea, QFrame
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData

from ClipboardCard import ClipboardCard
from PySide6.QtWidgets import QAbstractItemView
from ClipData import ClipData

class IClipboardTab:
    def populate_clipboard_list(self, clipboard_history):
        ...

class ClipboardTab(QWidget, IClipboardTab):
    clearRequested = Signal()
    def __init__(self):
        super().__init__()
        self.presenter = None 
        self.favorites_presenter = None
        self.id_to_list_item = {}
        self._setup_ui()
        self._set_styles()
        self._connect_signals()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        button_row = QHBoxLayout()
        button_row.addStretch()       # Push content to the right
        self.clear_button = QPushButton("Clear all")
        self.clear_button.setObjectName("clear_button")
        self.clear_button.setFixedSize(100, 50)
        button_row.addWidget(self.clear_button)
        root.addLayout(button_row)

        self.list = QListWidget()
        self.list.setObjectName("clipboard_list")
        self.list.setAlternatingRowColors(False)
        self.list.setResizeMode(QListWidget.Adjust)
        root.addWidget(self.list)

    def _set_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F7FB;
            }
            QFrame {
                background-color: #F5F7FB;
                margin: 0px;
                padding: 0px;
            }
            QPushButton#clear_button {
                background-color: #1A73E8;
                color: white;
                border-radius: 4px;
                padding: 0px;
                margin: 10px;
                min-width: 80px;
                text-transform: none; 
                font-size: 15px; 
                font-family: Ubuntu, sans-serif;
            }
            QPushButton#clear_button:hover {
                background-color: #2B7DE9;
            }

            QListWidget::item {
                margin: 5px;
                padding: 0px;
            }
            QListWidget#clipboard_list {
                spacing: 0px;
                padding: 0px;
            }
        """)
    
    def _connect_signals(self):
        self.clear_button.clicked.connect(self.clearRequested.emit)

    def add_list_item(self, id: str, clip_data: ClipData):
        list_item = QListWidgetItem()
        list_item_widget = ClipboardCard(id, clip_data)
        list_item_widget.copyRequested.connect(lambda mime_data: self.presenter.handle_copy_request(mime_data))
        list_item_widget.pasteRequested.connect(lambda mime_data: self.presenter.handle_paste_request(mime_data))
        list_item_widget.favRequested.connect(lambda id: self.handle_fav_request(id))
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.list.insertItem(0, list_item)
        self.list.setItemWidget(list_item, list_item_widget)
        self.id_to_list_item[id] = list_item
    
    def delete_list_item(self, id: str):
        self.list.takeItem(self.list.row(self.id_to_list_item[id]))
        del self.id_to_list_item[id]

    def clear_list(self):
        self.list.clear()
        self.id_to_list_item.clear()
    
    def handle_fav_request(self, id: str):
        self.presenter.handle_fav_request(id)
        self.favorites_presenter.handle_fav_request(id)

    def populate_clipboard_list(self, clipboard_history):
        """Populate clipboard list."""
        self.list.clear()
        for clip in clipboard_history:
            clip_data = ClipData.from_database(clip)
            self.add_list_item(clip['clip_id'], clip_data)

            
            