from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ClipData import ClipData
from ManualCard import ManualCard
from ManualDialog import ManualEntryDialog
from PageHeader import PageHeader
from resources import ADD_ICON_DARK


class ManualTab(QWidget):
    addRequested = Signal()
    searchRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.presenter = None
        self.id_to_list_item = {}
        self._delete_mode = False
        self._is_populating = False
        self._setup_ui()
        self._connect_signals()
        self._refresh_header()

    def _setup_ui(self):
        self.setObjectName("notes_tab")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = PageHeader(
            "Notes",
            "note",
            "Search notes",
        )
        self.add_button = self.header.add_primary_action(
            "New note",
            lambda checked=False: self.handle_add_request(),
            icon=ADD_ICON_DARK,
        )
        self.delete_action = self.header.add_menu_action(
            "Delete",
            self._set_delete_mode,
            checkable=True,
        )
        layout.addWidget(self.header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("notes_list")
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        layout.addWidget(self.list_widget)

    def _set_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: #f5f7fb;
            }
            QListWidget#notes_list {
                color: #202733;
                background: #f5f7fb;
                border: none;
                margin: 0;
                padding: 0;
                font-size: 15pt;
            }
            QListWidget#notes_list::item {
                margin: 5px;
                padding: 0;
            }
        """)

    def _connect_signals(self):
        self.header.searchChanged.connect(self.searchRequested.emit)

    def current_search_query(self) -> str:
        return self.header.current_search_text()

    def _set_delete_mode(self, enabled: bool) -> None:
        self._delete_mode = enabled
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            widget = self.list_widget.itemWidget(item)
            if widget is not None:
                widget.toggle_delete(enabled)

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
        list_item = self.id_to_list_item.pop(id, None)
        if list_item is not None:
            self.list_widget.takeItem(self.list_widget.row(list_item))
        self._refresh_header()

    def add_list_item(
        self,
        id: str,
        clip_data_top: ClipData,
        clip_data_bottom: ClipData,
    ):
        list_item = self.id_to_list_item.get(id)
        is_new_item = list_item is None
        if is_new_item:
            list_item = QListWidgetItem()

        list_item_widget = ManualCard(id, clip_data_top, clip_data_bottom)
        list_item_widget.toggle_delete(self._delete_mode)
        list_item_widget.copyRequested.connect(
            lambda mime_data: self.presenter.handle_copy_request(mime_data)
        )
        list_item_widget.pasteRequested.connect(
            lambda mime_data: self.presenter.handle_paste_request(mime_data)
        )
        list_item_widget.deleteRequested.connect(
            lambda note_id: self.presenter.handle_delete_request(note_id)
        )
        list_item_widget.editRequested.connect(
            lambda note_id: self.presenter.handle_edit_request(note_id)
        )
        list_item.setSizeHint(list_item_widget.sizeHint())

        if is_new_item:
            self.list_widget.insertItem(0, list_item)
            self.id_to_list_item[id] = list_item
        self.list_widget.setItemWidget(list_item, list_item_widget)

        if not self._is_populating:
            self._refresh_header()

    def _refresh_header(self) -> None:
        total = self.list_widget.count()
        if self.current_search_query():
            self.header.set_result_count(total)
        else:
            self.header.set_count(total)
        self.delete_action.setEnabled(total > 0)

    def populate_manual_list(self, notes_history):
        self.list_widget.clear()
        self.id_to_list_item.clear()
        self._is_populating = True
        try:
            for item in notes_history:
                clip_data_top = ClipData.from_database(item, data_key="title")
                clip_data_bottom = ClipData.from_database(
                    item,
                    data_key="preview_text",
                )
                self.add_list_item(
                    item["note_id"],
                    clip_data_top,
                    clip_data_bottom,
                )
        finally:
            self._is_populating = False
        self._refresh_header()
