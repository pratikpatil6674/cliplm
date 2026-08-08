from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ClipData import ClipData
from ClipboardCard import ClipboardCard
from PageHeader import PageHeader


class IClipboardTab:
    def populate_clipboard_list(self, clipboard_history):
        ...


class ClipboardTab(QWidget, IClipboardTab):
    clearRequested = Signal()
    searchRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.presenter = None
        self.favorites_presenter = None
        self.id_to_list_item = {}
        self._is_populating = False
        self._setup_ui()
        self._set_styles()
        self._connect_signals()
        self._refresh_header()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = PageHeader(
            "Clipboard history",
            "item",
            "Search history",
        )
        self.clear_action = self.header.add_menu_action(
            "Clear history...",
            lambda checked=False: self._confirm_clear(),
        )
        root.addWidget(self.header)

        self.list = QListWidget()
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setObjectName("clipboard_list")
        self.list.setAlternatingRowColors(False)
        self.list.setResizeMode(QListWidget.Adjust)
        root.addWidget(self.list)

    def _set_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fb;
            }
            QListWidget::item {
                margin: 5px;
                padding: 0;
            }
            QListWidget#clipboard_list {
                spacing: 0;
                padding: 0;
                border: none;
            }
        """)

    def _connect_signals(self):
        self.header.searchChanged.connect(self.searchRequested.emit)

    def current_search_query(self) -> str:
        return self.header.current_search_text()

    def _confirm_clear(self):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Clear clipboard history")
        message_box.setText("Clear every item from clipboard history?")
        message_box.setInformativeText("This action cannot be undone.")
        message_box.setIcon(QMessageBox.Warning)

        clear_button = message_box.addButton(
            "Clear history",
            QMessageBox.DestructiveRole,
        )
        cancel_button = message_box.addButton("Cancel", QMessageBox.RejectRole)
        message_box.setDefaultButton(cancel_button)
        clear_button.setIcon(QIcon())
        cancel_button.setIcon(QIcon())

        message_box.setStyleSheet("""
            QMessageBox {
                background: #f5f7fb;
            }
            QMessageBox QLabel {
                color: #1f2933;
                background: transparent;
                font-size: 11pt;
            }
            QMessageBox QPushButton {
                min-width: 96px;
                padding: 7px 12px;
                border: 1px solid #d5dce7;
                border-radius: 8px;
                background: #ffffff;
                color: #344054;
                font-size: 10pt;
                font-weight: 600;
                text-transform: none;
            }
        """)
        clear_button.setStyleSheet("""
            QPushButton {
                background: #cf3f4f;
                color: #ffffff;
                border: none;
            }
            QPushButton:hover {
                background: #b83242;
            }
        """)

        message_box.exec()
        if message_box.clickedButton() is clear_button:
            self.clearRequested.emit()

    def add_list_item(self, id: str, clip_data: ClipData):
        list_item = QListWidgetItem()
        list_item_widget = ClipboardCard(id, clip_data)
        list_item_widget.copyRequested.connect(
            lambda database_id: self.presenter.handle_copy_request(database_id)
        )
        list_item_widget.pasteRequested.connect(
            lambda database_id: self.presenter.handle_paste_request(database_id)
        )
        list_item_widget.favRequested.connect(
            lambda database_id: self.handle_fav_request(database_id)
        )
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.list.insertItem(0, list_item)
        self.list.setItemWidget(list_item, list_item_widget)
        self.id_to_list_item[id] = list_item
        if not self._is_populating:
            self._refresh_header()

    def delete_list_item(self, id: str):
        list_item = self.id_to_list_item.pop(id, None)
        if list_item is not None:
            self.list.takeItem(self.list.row(list_item))
        self._refresh_header()

    def clear_list(self):
        self.list.clear()
        self.id_to_list_item.clear()
        self._refresh_header()

    def _refresh_header(self) -> None:
        total = self.list.count()
        if self.current_search_query():
            self.header.set_result_count(total)
        else:
            self.header.set_count(total)
        self.clear_action.setEnabled(
            total > 0 or bool(self.current_search_query())
        )

    def handle_fav_request(self, id: str):
        self.presenter.handle_fav_request(id)
        self.favorites_presenter.handle_fav_request(id)

    def populate_clipboard_list(self, clipboard_history):
        self.list.clear()
        self.id_to_list_item.clear()
        self._is_populating = True
        try:
            for clip in clipboard_history:
                clip_data = ClipData.from_database(clip)
                self.add_list_item(clip["clip_id"], clip_data)
        finally:
            self._is_populating = False
        self._refresh_header()
