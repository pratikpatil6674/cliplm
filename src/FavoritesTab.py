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
import sys
from resources import *
from FavoriteCard import FavoriteCard
from ClipData import ClipData

class FavoritesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.presenter = None
        self._setup_ui()
        self._set_styles()
        self.id_to_list_item = {}

    def _setup_ui(self):
        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.delete_check = QCheckBox("Delete?")
        self.delete_check.setChecked(False)
        self.delete_check.stateChanged.connect(
            lambda event, t=self.list_widget: self.set_delete_btn_visibility(t)
        )

        self.layout.addWidget(self.delete_check)
        self.layout.addWidget(self.list_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.list_widget.setAlternatingRowColors(False)

    def _set_styles(self):
        self.list_widget.setStyleSheet(
            f"font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 0px; background-color: transparent;"
        )

    def set_delete_btn_visibility(self, list_widget: QListWidget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            widget.toggle_delete(self.delete_check.isChecked())
    
    def delete_list_item(self, id: str):
        self.list_widget.takeItem(self.list_widget.row(self.id_to_list_item[id]))
        del self.id_to_list_item[id]

    def add_list_item(self, id: str, clip_data: ClipData):
        list_item = QListWidgetItem()
        list_item_widget = FavoriteCard(id, clip_data)
        list_item_widget.toggle_delete(self.delete_check.isChecked())

        list_item_widget.copyRequested.connect(lambda mime_data: self.presenter.handle_copy_request(mime_data))
        list_item_widget.pasteRequested.connect(lambda mime_data: self.presenter.handle_paste_request(mime_data))
        list_item_widget.deleteRequested.connect(lambda id: self.presenter.handle_delete_request(id))
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.list_widget.insertItem(0, list_item)
        self.list_widget.setItemWidget(list_item, list_item_widget)
        self.id_to_list_item[id] = list_item

    def populate_fav_list(self, favorites_history):
        """Populate a list widget with data."""
        self.list_widget.clear()
        self.id_to_list_item.clear()
        for clip in favorites_history:
            clip_data = ClipData.from_database(clip)
            self.add_list_item(clip['clip_id'], clip_data)

            # list_item_widget.copyRequested.connect(lambda text: self.presenter.handle_copy_request(text))
            # list_item_widget.pasteRequested.connect(lambda text: self.presenter.handle_paste_request(text))
            # list_item_widget.deleteRequested.connect(lambda id: self.presenter.handle_delete_request(id))
            # list_item.setSizeHint(list_item_widget.sizeHint())
            # self.list_widget.addItem(list_item)
            # self.list_widget.setItemWidget(list_item, list_item_widget)
            # self.id_to_list_item[id] = list_item
