from pathlib import Path
from functools import partial
from typing import Optional

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QToolButton, QLabel, QSizePolicy
)
from PySide6.QtGui import QIcon, QFontMetrics
from PySide6.QtCore import Qt, Signal, QSize

# Example constants (use your resource resolution)
from resources import *


class ManualCard(QFrame):
    """
    Card widget representing a manual clipboard entry.

    Signals:
        copyRequested(str)   - emit the content to copy
        pasteRequested(str)  - emit the content to paste (or handle externally)
        deleteRequested(str) - emit the id to delete
        editRequested(str)   - emit the id to edit
    """

    copyRequested = Signal(str)
    pasteRequested = Signal(str)
    deleteRequested = Signal(str)
    editRequested = Signal(str,str,str)

    def __init__(
        self,
        top_text: str,
        bottom_text: str,
        manual_entry_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self.manual_entry_id = manual_entry_id
        self.top_text = top_text
        self.bottom_text = bottom_text

        self._setup_ui()
        self._setup_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setObjectName("manual_card")
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # Left icon column (vertical)
        icon_col = QVBoxLayout()
        icon_col.setSpacing(8)
        icon_col.addStretch()

        icon_size = QSize(20, 20)  # design-scale icon size

        self.copy_btn = QToolButton()
        self.copy_btn.setIcon(COPY_ICON)
        self.copy_btn.setIconSize(icon_size)
        self.copy_btn.setToolTip("Copy")
        self.copy_btn.setAutoRaise(True)  # flat look
        icon_col.addWidget(self.copy_btn)
        icon_col.addStretch()

        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(DELETE_ICON)
        self.delete_btn.setIconSize(icon_size)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.setAutoRaise(True)
        icon_col.addWidget(self.delete_btn)
        icon_col.addStretch()


        self.delete_button_placeholder = QToolButton()
        self.delete_button_placeholder.setFixedSize(icon_size)
        self.delete_button_placeholder.hide()
        icon_col.addWidget(self.delete_button_placeholder)

        # Text column (right)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        self.top_label = QLabel(self.top_text)
        self.top_label.setObjectName("manual_card_top")
        self.top_label.setWordWrap(False)
        self.top_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.top_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.top_label.setToolTip(self.top_text)

        self.bottom_label = QLabel(self.bottom_text)
        self.bottom_label.setObjectName("manual_card_bottom")
        self.bottom_label.setWordWrap(True)
        self.bottom_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bottom_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ensure descenders not clipped
        fm = QFontMetrics(self.bottom_label.font())
        min_h = fm.lineSpacing() + 6
        self.bottom_label.setMinimumHeight(min_h)

        text_col.addWidget(self.top_label)
        text_col.addWidget(self.bottom_label)

        # edit button on the far right
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(EDIT_ICON)
        self.edit_btn.setIconSize(icon_size)
        self.edit_btn.setToolTip("Edit")
        self.edit_btn.setAutoRaise(True)

        layout.addLayout(icon_col)
        layout.addLayout(text_col)
        layout.addWidget(self.edit_btn, alignment=Qt.AlignTop)

    def _setup_styles(self) -> None:
        # Small, local stylesheet. Prefer app-wide QSS for bigger projects.
        self.setStyleSheet(
            """
            QFrame#manual_card {
                background: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QFrame#manual_card:hover {
                border: 1px solid #2979ff;
            }
            QLabel#manual_card_top {
                color: #7a7a7a;
                font-size: 12px;
            }
            QLabel#manual_card_bottom {
                color: #111111;
                font-size: 14px;
            }
            QToolButton {
                background: transparent;
                border: none;
            }
            QToolButton:hover {
                background: rgba(0,0,0,0.04);
                border-radius: 4px;
            }
            """
        )

    def _connect_signals(self) -> None:
        # Use partials or instance methods to avoid late-binding issues in loops
        self.copy_btn.clicked.connect(partial(self._on_copy_clicked))
        self.delete_btn.clicked.connect(partial(self._on_delete_clicked))
        self.edit_btn.clicked.connect(partial(self._on_edit_clicked))

        # If you want clicking the labels to paste:
        self.top_label.mousePressEvent = partial(self._on_label_clicked, text=self.top_text)
        self.bottom_label.mousePressEvent = partial(self._on_label_clicked, text=self.bottom_text)
    
    def toggle_delete(self, visible: bool):
        self.delete_btn.setVisible(visible)
        self.delete_button_placeholder.setVisible(not visible)

    # --- private slots ---
    def _on_copy_clicked(self):
        self.copyRequested.emit(self.bottom_text)

    def _on_delete_clicked(self):
        self.deleteRequested.emit(self.manual_entry_id)

    def _on_edit_clicked(self):
        self.editRequested.emit(self.manual_entry_id, self.top_text, self.bottom_text)

    def _on_label_clicked(self, event, text: str):
        # If you want left click only:
        if event.button() == Qt.LeftButton:
            self.pasteRequested.emit(text)

    # Optional: convenience setters
    def update_texts(self, top_text: Optional[str] = None, bottom_text: Optional[str] = None):
        if top_text is not None:
            self.top_text = top_text
            self.top_label.setText(top_text)
            self.top_label.setToolTip(top_text)
        if bottom_text is not None:
            self.bottom_text = bottom_text
            self.bottom_label.setText(bottom_text)
