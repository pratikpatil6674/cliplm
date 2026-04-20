from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QStyle, QVBoxLayout, QWidget, QStackedWidget

from SidebarTabButton import SidebarTabButton
from resources import *


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records = []
        self._current_index = -1
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
        self.top_tabs_layout.setSpacing(1)
        sidebar_layout.addLayout(self.top_tabs_layout)
        sidebar_layout.addStretch(1)

        self.bottom_tabs_layout = QVBoxLayout()
        self.bottom_tabs_layout.setSpacing(4)
        sidebar_layout.addLayout(self.bottom_tabs_layout)

        self.content_shell = QFrame()
        self.content_shell.setObjectName("content_shell")
        content_layout = QVBoxLayout(self.content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("sidebar_pages")
        content_layout.addWidget(self.stack)

        root.addWidget(self.sidebar)
        root.addWidget(self.content_shell, 1)

        # Give the stacked content its own solid surface so hidden pages do not
        # visually bleed through when switching tabs.
        self._base_stylesheet = """
            QFrame#sidebar_tabs {
                background: #fbfdff;
                border-right: 1px solid rgba(30,36,44,0.08);
            }
            QFrame#content_shell {
                background: #f5f7fb;
            }
            QStackedWidget#sidebar_pages {
                background: #f5f7fb;
            }
        """
        super().setStyleSheet(self._base_stylesheet)

    def addTab(self, widget, tab_name):
        display_text = self._display_text_for_tab(tab_name)
        icon_dark, icon_light = self._default_icon_for_text(tab_name)

        button = SidebarTabButton(display_text, icon_dark, self.sidebar)
        button.clicked.connect(lambda checked=False, index=len(self._records): self.setCurrentIndex(index))

        # Each tab page gets a dedicated wrapper so the stacked widget always
        # swaps full-size pages instead of exposing content from another page.
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(widget)

        record = _TabRecord(widget=widget, page=page, button=button, text=tab_name, icon=icon_dark, icon_light=icon_light)
        self._records.append(record)
        self.stack.addWidget(page)

        target_layout = self.bottom_tabs_layout if self._dock_to_bottom(tab_name) else self.top_tabs_layout
        target_layout.addWidget(button, 0, Qt.AlignHCenter)

        if self._current_index == -1:
            self.setCurrentIndex(0)

        return len(self._records) - 1

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
            record.button.setChecked(button_index == index)
            record.button.setIcon(record.icon_light if button_index == index else record.icon)
            record.button.update()
        self.currentChanged.emit(index)

    def setCurrentWidget(self, widget):
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)

    def setTabPosition(self, position):
        # Compatibility no-op so App.py can stay almost unchanged.
        return None

    def setStyleSheet(self, styleSheet):
        merged_stylesheet = self._base_stylesheet
        if styleSheet:
            merged_stylesheet = f"{merged_stylesheet}\n{styleSheet}"
        super().setStyleSheet(merged_stylesheet)

    def _first_visible_index(self):
        for index, record in enumerate(self._records):
            if record.visible:
                return index
        return -1

    def _parse_add_tab_args(self, *args):
        if len(args) == 1:
            return QIcon(), str(args[0])
        if len(args) == 2:
            return args[0], str(args[1])
        raise TypeError("addTab expects (widget, text) or (widget, icon, text)")

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
        key = text.strip().casefold()
        if key == "clipboard":
            return CLIP_ICON, CLIP_ICON_LIGHT
        if key == "favorites":
            return STAR_ICON, STAR_ICON_LIGHT
        if key == "notes":
            return NOTE_ICON, NOTE_ICON_LIGHT
        if key == "translate":
            return TRANSLATE_ICON, TRANSLATE_ICON_LIGHT
        if key == "agent":
            return AI_ICON, AI_ICON_LIGHT
        if key == "settings":
            return SETTINGS_ICON, SETTINGS_ICON_LIGHT
        return QIcon(), QIcon()
