
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QListWidget, QPushButton, QLabel,
    QHBoxLayout, QTextEdit, QListWidgetItem, QDialog, QCheckBox, QScrollArea, QFrame
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon,
    QMenu
)
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon

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
        self.clear_button.setFixedSize(100, 40)
        button_row.addWidget(self.clear_button)
        root.addLayout(button_row)

        self.list = QListWidget()
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
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
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                margin: 5px;
                padding: 6px 12px;
                border-radius: 8px;
                min-width: 80px;
                text-transform: none; 
                font-size: 12pt;
                font-weight: 600;
            }
            QPushButton#clear_button:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
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
        self.clear_button.clicked.connect(self._confirm_clear)

    def _confirm_clear(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Clear Clipboard")
        message_box.setText("Clear all clipboard items?")
        message_box.setIcon(QMessageBox.Warning)
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)
        message_box.setStyleSheet("""
            QMessageBox {
                background: #f5f7fb;
            }
            QMessageBox QLabel {
                color: #1f2933;
                font-size: 12pt;
                background: transparent;
            }
            QMessageBox QPushButton {
                min-width: 96px;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12pt;
                text-transform: none;
            }
        """)

        yes_button = message_box.button(QMessageBox.Yes)
        no_button = message_box.button(QMessageBox.No)
        if yes_button is not None:
            yes_button.setIcon(QIcon())
            yes_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                    color: #fff;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 12pt;
                    text-transform: none;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
                }
            """)
        if no_button is not None:
            no_button.setIcon(QIcon())
            no_button.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    color: #2c62d6;
                    border: 1px solid rgba(44,98,214,0.18);
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 12pt;
                    text-transform: none;
                }
                QPushButton:hover {
                    background: #f0f5ff;
                }
            """)

        if message_box.exec() == QMessageBox.Yes:
            self.clearRequested.emit()

    def add_list_item(self, id: str, clip_data: ClipData):
        list_item = QListWidgetItem()
        list_item_widget = ClipboardCard(id, clip_data)
        list_item_widget.copyRequested.connect(lambda id: self.presenter.handle_copy_request(id))
        list_item_widget.pasteRequested.connect(lambda id: self.presenter.handle_paste_request(id))
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

            
            
