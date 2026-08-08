from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget,
)


class _SearchLineEdit(QLineEdit):
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)


class PageHeader(QFrame):
    """Shared title, count, search, and action row for list-based pages."""

    searchChanged = Signal(str)

    def __init__(
        self,
        title: str,
        item_name: str,
        search_placeholder: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._item_name = item_name
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._emit_search)
        self.setObjectName("page_header")
        self._setup_ui(title, search_placeholder)
        self._set_styles()

    def _setup_ui(self, title: str, search_placeholder: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 9, 10, 9)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("page_title")

        self.count_label = QLabel()
        self.count_label.setObjectName("page_count")

        self.search_field = _SearchLineEdit()
        self.search_field.setObjectName("page_search")
        self.search_field.setFocusPolicy(Qt.ClickFocus)
        self.search_field.setPlaceholderText(search_placeholder)
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setFixedWidth(170)
        self.search_field.setFixedHeight(32)
        self.search_field.textChanged.connect(self._queue_search)

        self.actions_widget = QWidget()
        self.actions_widget.setObjectName("page_header_actions")
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(6)

        self.overflow_menu = QMenu(self)
        self.overflow_menu.setObjectName("page_overflow_menu")
        self.overflow_button = QToolButton()
        self.overflow_button.setObjectName("page_overflow_button")
        self.overflow_button.setText("...")
        self.overflow_button.setToolTip("More options")
        self.overflow_button.setCursor(Qt.PointingHandCursor)
        self.overflow_button.setPopupMode(QToolButton.InstantPopup)
        self.overflow_button.setMenu(self.overflow_menu)
        self.overflow_button.setFixedSize(32, 32)
        self.overflow_button.hide()

        layout.addWidget(self.title_label)
        layout.addWidget(self.count_label)
        layout.addStretch(1)
        layout.addWidget(self.search_field)
        layout.addWidget(self.actions_widget)
        layout.addWidget(self.overflow_button)

        self.set_count(0)

    def add_primary_action(
        self,
        text: str,
        callback,
        icon: QIcon | None = None,
    ) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("page_primary_action")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(32)
        if icon is not None:
            button.setIcon(icon)
        button.clicked.connect(callback)
        self.actions_layout.addWidget(button)
        return button

    def add_menu_action(
        self,
        text: str,
        callback,
        *,
        icon: QIcon | None = None,
        checkable: bool = False,
    ) -> QAction:
        action = QAction(icon or QIcon(), text, self)
        action.setCheckable(checkable)
        action.triggered.connect(callback)
        self.overflow_menu.addAction(action)
        self.overflow_button.show()
        return action

    def set_count(self, total: int, visible: int | None = None) -> None:
        if visible is not None and visible != total:
            self.count_label.setText(f"{visible} of {total}")
            return

        suffix = self._item_name if total == 1 else f"{self._item_name}s"
        self.count_label.setText(f"{total} {suffix}")

    def set_result_count(self, total: int) -> None:
        suffix = "result" if total == 1 else "results"
        self.count_label.setText(f"{total} {suffix}")

    def current_search_text(self) -> str:
        return self.search_field.text().strip()

    def focus_search(self) -> None:
        self.search_field.setFocus(Qt.ShortcutFocusReason)
        self.search_field.selectAll()

    def _queue_search(self, _text: str) -> None:
        # Avoid querying SQLite for every key press.
        self._search_timer.start()

    def _emit_search(self) -> None:
        self.searchChanged.emit(self.current_search_text())

    def _set_styles(self) -> None:
        self.setStyleSheet("""
            QFrame#page_header {
                background: #f5f7fb;
                border: none;
                border-bottom: 1px solid rgba(30, 36, 44, 0.08);
            }
            QLabel#page_title {
                color: #202733;
                background: transparent;
                font-size: 14pt;
                font-weight: 700;
            }
            QLabel#page_count {
                color: #687386;
                background: #e9edf4;
                border-radius: 9px;
                padding: 2px 7px;
                font-size: 9pt;
            }
            QLineEdit#page_search {
                color: #202733;
                background: #ffffff;
                border: 1px solid #d5dce7;
                border-radius: 8px;
                padding: 0 9px;
                font-size: 10pt;
                selection-background-color: #2f6fe4;
            }
            QLineEdit#page_search:hover {
                border-color: #aebbd0;
                background: #fbfdff;
            }
            QLineEdit#page_search:focus {
                border: 1px solid #2f6fe4;
                background: #ffffff;
            }
            QPushButton#page_primary_action {
                color: #ffffff;
                background: #2f6fe4;
                border: none;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 10pt;
                font-weight: 600;
                text-transform: none;
            }
            QPushButton#page_primary_action:hover {
                background: #255fc8;
            }
            QToolButton#page_overflow_button {
                color: #4b5668;
                background: transparent;
                border: none;
                border-radius: 7px;
                padding: 0;
                font-size: 15pt;
                font-weight: 700;
            }
            QToolButton#page_overflow_button:hover,
            QToolButton#page_overflow_button:pressed {
                color: #202733;
                background: #e7ecf4;
            }
            QToolButton#page_overflow_button::menu-indicator {
                image: none;
            }
            QMenu#page_overflow_menu {
                color: #202733;
                background: #ffffff;
                border: none;
                padding: 2px;
                font-size: 10pt;
            }
            QMenu#page_overflow_menu::item {
                border: none;
                border-radius: 5px;
                margin: 0;
                padding: 5px 11px;
                min-height: 18px;
            }
            QMenu#page_overflow_menu::item:selected {
                background: #edf3ff;
                color: #255fc8;
            }
        """)


