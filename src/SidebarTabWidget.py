from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from SidebarTabButton import SidebarTabButton
from resources import (
    AI_ICON,
    AI_ICON_LIGHT,
    CLIP_ICON,
    CLIP_ICON_LIGHT,
    NOTE_ICON,
    NOTE_ICON_LIGHT,
    SETTINGS_ICON,
    SETTINGS_ICON_LIGHT,
    STAR_ICON,
    STAR_ICON_LIGHT,
    SYNC_ICON_DARK,
    SYNC_ICON_LIGHT,
    TRANSLATE_ICON,
    TRANSLATE_ICON_LIGHT,
)


@dataclass
class _TabRecord:
    widget: QWidget
    page: QWidget
    button: SidebarTabButton
    text: str
    icon: QIcon
    icon_light: QIcon
    visible: bool = True


class SidebarTabWidget(QWidget):
    currentChanged = Signal(int)
    updateRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records = []
        self._current_index = -1
        self._available_update_version = ""
        self._dark_mode = False
        self._setup_ui()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar_tabs")
        self.sidebar.setFixedWidth(60)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.top_tabs_layout = QVBoxLayout()
        self.top_tabs_layout.setContentsMargins(0, 4, 0, 0)
        self.top_tabs_layout.setSpacing(1)
        sidebar_layout.addLayout(self.top_tabs_layout)
        sidebar_layout.addStretch(1)

        self.bottom_tabs_layout = QVBoxLayout()
        self.bottom_tabs_layout.setSpacing(4)

        self.update_button = SidebarTabButton(
            "Updates",
            SYNC_ICON_DARK,
            self.sidebar,
        )
        self.update_button.setCheckable(False)
        self.update_button.setToolTip("Check for ClipLM updates")
        self.update_button.clicked.connect(self.updateRequested.emit)

        self.update_badge = QFrame(self.update_button)
        self.update_badge.setObjectName("update_badge")
        self.update_badge.setFixedSize(9, 9)
        self.update_badge.move(33, 2)
        self.update_badge.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.update_badge.hide()
        self.bottom_tabs_layout.addWidget(
            self.update_button,
            0,
            Qt.AlignHCenter,
        )
        sidebar_layout.addLayout(self.bottom_tabs_layout)

        self.content_shell = QFrame()
        self.content_shell.setObjectName("content_shell")
        self.content_shell.setAttribute(Qt.WA_StyledBackground, True)
        content_layout = QVBoxLayout(self.content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)


        self.stack = QStackedWidget()
        self.stack.setObjectName("sidebar_pages")
        self.stack.setAttribute(Qt.WA_StyledBackground, True)
        content_layout.addWidget(self.stack)

        self.search_shortcut = QShortcut(QKeySequence("/"), self)
        self.search_shortcut.setContext(Qt.WindowShortcut)
        self.search_shortcut.activated.connect(self._focus_current_page_search)
        self.search_shortcut.setEnabled(False)

        root.addWidget(self.sidebar)
        root.addWidget(self.content_shell, 1)

    def addTab(self, widget, tab_name):
        display_text = self._display_text_for_tab(tab_name)
        icon_dark, icon_light = self._default_icon_for_text(tab_name)

        button = SidebarTabButton(display_text, icon_dark, self.sidebar)
        button.clicked.connect(
            lambda checked=False, index=len(self._records): self.setCurrentIndex(
                index
            )
        )

        page = QWidget()
        page.setObjectName("sidebar_page")
        page.setAttribute(Qt.WA_StyledBackground, True)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(widget)

        record = _TabRecord(
            widget=widget,
            page=page,
            button=button,
            text=tab_name,
            icon=icon_dark,
            icon_light=icon_light,
        )
        self._records.append(record)
        self.stack.addWidget(page)

        target_layout = (
            self.bottom_tabs_layout
            if self._dock_to_bottom(tab_name)
            else self.top_tabs_layout
        )
        target_layout.addWidget(button, 0, Qt.AlignHCenter)

        if self._current_index == -1:
            self.setCurrentIndex(0)

        return len(self._records) - 1

    def set_update_available(self, available: bool, version: str = "") -> None:
        self._available_update_version = version if available else ""
        self.update_badge.setVisible(available)
        if available:
            self.update_button.setToolTip(
                f"ClipLM {version} is available" if version else "Update available"
            )
        else:
            self.update_button.setToolTip("ClipLM is up to date")

    def count(self):
        return len(self._records)

    def currentIndex(self):
        return self._current_index

    def currentWidget(self):
        if 0 <= self._current_index < len(self._records):
            return self._records[self._current_index].widget
        return None

    def widget(self, index):
        return self._records[index].widget

    def indexOf(self, widget):
        for index, record in enumerate(self._records):
            if record.widget is widget:
                return index
        return -1

    def tabText(self, index):
        return self._records[index].text

    def isTabVisible(self, index):
        return self._records[index].visible

    def setTabVisible(self, index, visible):
        record = self._records[index]
        record.visible = visible
        record.button.setVisible(visible)
        record.page.setVisible(visible)

        if visible:
            if self._current_index == -1:
                self.setCurrentIndex(index)
            return

        if index == self._current_index:
            fallback_index = self._first_visible_index()
            self._current_index = -1
            if fallback_index != -1:
                self.setCurrentIndex(fallback_index)
            else:
                self.stack.setCurrentIndex(-1)

    def setCurrentIndex(self, index):
        if index < 0 or index >= len(self._records):
            return
        if not self._records[index].visible:
            return

        self._current_index = index
        self.stack.setCurrentWidget(self._records[index].page)
        for button_index, record in enumerate(self._records):
            is_current = button_index == index
            record.button.setChecked(is_current)
            if self._dark_mode:
                icon = record.icon if is_current else record.icon_light
            else:
                icon = record.icon_light if is_current else record.icon
            record.button.setIcon(icon)
            record.button.update()
        self.currentChanged.emit(index)
        self._update_search_shortcut()


    def set_dark_mode(self, enabled: bool) -> None:
        self._dark_mode = bool(enabled)
        self.update_button.setIcon(
            SYNC_ICON_LIGHT if self._dark_mode else SYNC_ICON_DARK
        )
        if self._current_index >= 0:
            self.setCurrentIndex(self._current_index)

    def _update_search_shortcut(self) -> None:
        current_widget = self.currentWidget()
        header = getattr(current_widget, "header", None)
        self.search_shortcut.setEnabled(
            callable(getattr(header, "focus_search", None))
        )

    def _focus_current_page_search(self) -> None:
        current_widget = self.currentWidget()
        header = getattr(current_widget, "header", None)
        if header is None:
            return

        if header.search_field.hasFocus():
            header.search_field.insert("/")
            return
        header.focus_search()

    def setCurrentWidget(self, widget):
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)

    def setTabPosition(self, position):
        return None

    def _first_visible_index(self):
        for index, record in enumerate(self._records):
            if record.visible:
                return index
        return -1

    def _dock_to_bottom(self, text: str):
        return text.strip().casefold() == "settings"

    def _display_text_for_tab(self, text: str):
        labels = {
            "clipboard": "Clips",
            "favorites": "Faves",
            "notes": "Notes",
            "translate": "Trans.",
            "agent": "Agent",
            "settings": "Settings",
        }
        return labels.get(text.strip().casefold(), text)

    def _default_icon_for_text(self, text: str):
        icons = {
            "clipboard": (CLIP_ICON, CLIP_ICON_LIGHT),
            "favorites": (STAR_ICON, STAR_ICON_LIGHT),
            "notes": (NOTE_ICON, NOTE_ICON_LIGHT),
            "translate": (TRANSLATE_ICON, TRANSLATE_ICON_LIGHT),
            "agent": (AI_ICON, AI_ICON_LIGHT),
            "settings": (SETTINGS_ICON, SETTINGS_ICON_LIGHT),
        }
        return icons.get(text.strip().casefold(), (QIcon(), QIcon()))
