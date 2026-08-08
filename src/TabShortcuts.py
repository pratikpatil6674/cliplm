import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


class TabShortcuts:
    def __init__(self, parent, tab_widget):
        self.parent = parent
        self.tab_widget = tab_widget
        self.shortcuts = []
        self._install_shortcuts()

    def _install_shortcuts(self):
        initials = {
            self.tab_widget.tabText(index).strip()[0].lower()
            for index in range(self.tab_widget.count())
            if self.tab_widget.tabText(index).strip()
        }

        for initial in initials:
            shortcut = QShortcut(QKeySequence(initial), self.parent)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(
                lambda key=initial: self.focus_tab_by_initial(key)
            )
            self.shortcuts.append(shortcut)

    def focus_tab_by_initial(self, initial):
        matches = []
        for index in range(self.tab_widget.count()):
            label = self.tab_widget.tabText(index).strip()
            if not label:
                continue
            if not self.tab_widget.isTabVisible(index):
                continue
            if label[0].lower() == initial.lower():
                matches.append(index)

        if not matches:
            return

        current_index = self.tab_widget.currentIndex()
        if current_index in matches:
            current_widget = self.tab_widget.currentWidget()
            trigger_primary_action = getattr(
                current_widget,
                "trigger_primary_action",
                None,
            )
            if callable(trigger_primary_action):
                trigger_primary_action()
                return

        self.tab_widget.setCurrentIndex(random.choice(matches))
