
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
    QScrollArea,
    QFrame,
    QSizePolicy,
    QAbstractItemView
)
from PySide6.QtGui import QIcon
import sys
from resources import *
from FavoriteCard import FavoriteCard
from PySide6.QtCore import Signal
from ManualDialog import ManualEntryDialog
from ManualCard import ManualCard
from PySide6.QtGui import QColor

from ClipData import ClipData

class ManualTab(QWidget):
    addRequested = Signal()
    def __init__(self):
        super().__init__()
        self.presenter = None
        self.id_to_list_item = {}
        self._setup_ui()
        self._set_styles()
        self._connect_signals()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.delete_check = QCheckBox("Delete?")
        self.delete_check.setChecked(False)
        self.add_button = QPushButton("+ New note")
        self.add_button.setFixedSize(100, 40)
        self.list_widget = QListWidget()

        top_row_layout = QHBoxLayout()
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.addWidget(self.add_button)
        top_row_layout.addWidget(self.delete_check)
        top_row_layout.addStretch()

        self.layout.addLayout(top_row_layout)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.layout.addWidget(self.list_widget)

    def _set_styles(self):
        self.setStyleSheet(f"background: #F5F7FB; ")
        self.add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                margin: 5px;
                padding: 6px 12px;
                border-radius: 8px;
                min-width: 80px;
                text-transform: none; 
                font-size: 15px;
                font-family: Ubuntu, sans-serif;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
        """)
        self.list_widget.setStyleSheet("""
            padding: 0px; 
            margin: 0px; 
            background-color: #F5F7FB;
            font-size: 15px; 
            font-family: Ubuntu, sans-serif; 
        """)

    def set_delete_btn_visibility(self, state, list_widget: QListWidget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            widget.toggle_delete(state)
    
    def _connect_signals(self):
        self.add_button.clicked.connect(self.handle_add_request)
        self.delete_check.stateChanged.connect(lambda state, t=self.list_widget: self.set_delete_btn_visibility(state, t))
    
    def handle_add_request(self):
        self.addRequested.emit()

    def get_manual_entry(self, init_title: str = "", init_text: str = ""):
        dialog = ManualEntryDialog(self, init_title, init_text)
        if dialog.exec() == QDialog.Accepted:
            title, text = dialog.get_inputs()
            if title.strip() and text.strip():
                return title, text
        return None, None
    
    def delete_list_item(self, id: str):
        self.list_widget.takeItem(self.list_widget.row(self.id_to_list_item[id]))
        del self.id_to_list_item[id]
        
    def add_list_item(self, id: str, clip_data_top: ClipData, clip_data_bottom: ClipData):
        if id in self.id_to_list_item:
            print(f"Updating existing item with id: {id}")
            list_item = self.id_to_list_item[id]
        else:
            list_item = QListWidgetItem()
            
        list_item_widget = ManualCard(id, clip_data_top, clip_data_bottom)
        list_item_widget.toggle_delete(self.delete_check.isChecked())
        list_item_widget.copyRequested.connect(lambda mime_data: self.presenter.handle_copy_request(mime_data))
        list_item_widget.pasteRequested.connect(lambda mime_data: self.presenter.handle_paste_request(mime_data))
        list_item_widget.deleteRequested.connect(lambda id: self.presenter.handle_delete_request(id))
        list_item_widget.editRequested.connect(lambda id: self.presenter.handle_edit_request(id))
        list_item.setSizeHint(list_item_widget.sizeHint())
        if id not in self.id_to_list_item:
            print(f"Adding new item with id: {id}")
            self.list_widget.insertItem(0, list_item)
            self.id_to_list_item[id] = list_item
        else:
            print(f"Updated existing item with id: {id}")
        self.list_widget.setItemWidget(list_item, list_item_widget)
        
    def populate_manual_list(self, notes_history):
        """Populate a list widget with data."""
        self.list_widget.clear()
        self.id_to_list_item.clear()
        self.list_widget.setAlternatingRowColors(False)
        for item in notes_history:
            clip_data_top = ClipData.from_database(item, data_key='title')
            clip_data_bottom = ClipData.from_database(item, data_key='preview_text')
            self.add_list_item(item['note_id'], clip_data_top, clip_data_bottom)
            