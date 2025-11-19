
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
)
from PySide6.QtGui import QIcon
import sys
from resources import *
from FavoriteCard import FavoriteCard
from PySide6.QtCore import Signal
from ManualDialog import ManualEntryDialog
from ManualCard import ManualCard
from PySide6.QtGui import QColor

class ManualTab(QWidget):
    addRequested = Signal()
    def __init__(self):
        super().__init__()
        self.presenter = None
        self._setup_ui()
        self._set_styles()
        self._connect_signals()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.add_button = QPushButton("Add note")
        self.delete_check = QCheckBox("Delete?")
        self.delete_check.setChecked(False)

        self.layout.addWidget(self.delete_check)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.add_button)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def _set_styles(self):
        self.add_button.setStyleSheet(f" color: white; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 10px; background-color: #1A73E8;")
        self.list_widget.setStyleSheet(f"font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 0px; background-color: transparent;")

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
    
    def populate_manual_list(self, data):
        """Populate a list widget with data."""
        self.list_widget.clear()
        self.list_widget.setAlternatingRowColors(False)
        for index, (manual_entry_id, entry) in enumerate(data.items()):
            list_item = QListWidgetItem()
            list_item_widget = ManualCard(entry[0], entry[1], manual_entry_id)
            list_item_widget.toggle_delete(self.delete_check.isChecked())
            # list_item_widget = manual_card(entry['title'], entry['text'], self.copy_text, self.paste_text, self.delete_manual_entry, self.add_manual_entry, manual_entry_id)
            list_item_widget.copyRequested.connect(lambda text: self.presenter.handle_copy_request(text))
            list_item_widget.pasteRequested.connect(lambda text: self.presenter.handle_paste_request(text))
            list_item_widget.deleteRequested.connect(lambda id: self.presenter.handle_delete_request(id))
            list_item_widget.editRequested.connect(lambda id, title, text: self.presenter.handle_edit_request(id, title, text))

            list_item.setSizeHint(list_item_widget.sizeHint())
            # list_item.mousePressEvent = lambda event, t=entry['text']: self.paste_manual_text(event, t)
            bg_color = QColor(255, 0, 0) if index % 2 == 0 else QColor(220, 220, 220)
            list_item.setForeground(bg_color)  # Light gray
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, list_item_widget)
