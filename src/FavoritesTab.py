from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ClipData import ClipData
from FavoriteCard import FavoriteCard
from PageHeader import PageHeader


class FavoritesTab(QWidget):
    searchRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.presenter = None
        self.id_to_list_item = {}
        self._manage_mode = False
        self._is_populating = False
        self._setup_ui()
        self._set_styles()
        self._connect_signals()
        self._refresh_header()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = PageHeader(
            "Saved favorites",
            "favorite",
            "Search favorites",
        )
        self.manage_action = self.header.add_menu_action(
            "Manage favorites",
            self._set_manage_mode,
            checkable=True,
        )
        layout.addWidget(self.header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("favorites_list")
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        layout.addWidget(self.list_widget)

    def _set_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: #f5f7fb;
            }
            QListWidget#favorites_list {
                color: #202733;
                background: #f5f7fb;
                border: none;
                margin: 0;
                padding: 0;
                font-size: 15pt;
            }
            QListWidget#favorites_list::item {
                margin: 5px;
                padding: 0;
            }
        """)

    def _connect_signals(self):
        self.header.searchChanged.connect(self.searchRequested.emit)

    def current_search_query(self) -> str:
        return self.header.current_search_text()

    def _set_manage_mode(self, enabled: bool) -> None:
        self._manage_mode = enabled
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            widget = self.list_widget.itemWidget(item)
            if widget is not None:
                widget.toggle_delete(enabled)

    def delete_list_item(self, id: str):
        list_item = self.id_to_list_item.pop(id, None)
        if list_item is not None:
            self.list_widget.takeItem(self.list_widget.row(list_item))
        self._refresh_header()

    def add_list_item(self, id: str, clip_data: ClipData):
        list_item = QListWidgetItem()
        list_item_widget = FavoriteCard(id, clip_data)
        list_item_widget.toggle_delete(self._manage_mode)
        list_item_widget.copyRequested.connect(
            lambda database_id: self.presenter.handle_copy_request(database_id)
        )
        list_item_widget.pasteRequested.connect(
            lambda database_id: self.presenter.handle_paste_request(database_id)
        )
        list_item_widget.deleteRequested.connect(
            lambda database_id: self.presenter.handle_delete_request(database_id)
        )
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.list_widget.insertItem(0, list_item)
        self.list_widget.setItemWidget(list_item, list_item_widget)
        self.id_to_list_item[id] = list_item
        if not self._is_populating:
            self._refresh_header()

    def _refresh_header(self) -> None:
        total = self.list_widget.count()
        if self.current_search_query():
            self.header.set_result_count(total)
        else:
            self.header.set_count(total)
        self.manage_action.setEnabled(total > 0)

    def populate_fav_list(self, favorites_history):
        self.list_widget.clear()
        self.id_to_list_item.clear()
        self._is_populating = True
        try:
            for clip in favorites_history:
                clip_data = ClipData.from_database(clip)
                self.add_list_item(clip["clip_id"], clip_data)
        finally:
            self._is_populating = False
        self._refresh_header()
