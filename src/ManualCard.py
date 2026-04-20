from pathlib import Path
from functools import partial
from typing import Optional

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QToolButton, QLabel, QSizePolicy
)
from PySide6.QtGui import QIcon, QFontMetrics
from PySide6.QtCore import Qt, Signal, QSize

from ClipData import ClipData
# Example constants (use your resource resolution)
from resources import *


class ManualCard(QFrame):
    """
    Card widget representing a manual clipboard entry.
    """

    copyRequested = Signal(QMimeData)
    pasteRequested = Signal(QMimeData)
    deleteRequested = Signal(str)
    editRequested = Signal(str)
    MAX_CARD_HEIGHT = 180
    
    def __init__(
        self,
        id: str,
        clip_data_top: ClipData,
        clip_data_bottom: ClipData,
    ):
        super().__init__()
        self.id = id
        self.clip_data_top = clip_data_top
        self.clip_data_bottom = clip_data_bottom

        self._setup_ui()
        self._setup_styles()
        self._connect_signals()

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(min(hint.height(), self.MAX_CARD_HEIGHT))
        return hint

    def _setup_ui(self) -> None:
        self.setObjectName("manual_card")
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        # layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        # Left icon column (vertical)
        icon_col = QVBoxLayout()
        # icon_col.setSpacing(8)
        icon_col.addStretch()

        icon_size = QSize(18, 18)  # design-scale icon size

        self.copy_btn = QToolButton()
        self.copy_btn.setIcon(COPY_ICON_LIGHT)
        self.copy_btn.setIconSize(icon_size)
        self.copy_btn.setToolTip("Copy")
        self.copy_btn.setAutoRaise(True)  # flat look
        icon_col.addWidget(self.copy_btn)
        icon_col.addStretch()

        self.delete_btn = QToolButton()
        self.delete_btn.setIcon(DELETE_ICON_LIGHT)
        self.delete_btn.setIconSize(icon_size)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.setAutoRaise(True)
        icon_col.addWidget(self.delete_btn)
        icon_col.addStretch()


        self.delete_button_placeholder = QToolButton()
        self.delete_button_placeholder.setObjectName("placeholder")
        self.delete_button_placeholder.setFixedSize(icon_size)
        self.delete_button_placeholder.hide()
        icon_col.addWidget(self.delete_button_placeholder)

        # Text column (right)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        self.title_widget = self.clip_data_top.create_preview_widget(max_height=30)
        self.title_widget.setObjectName("manual_card_top")
        self.desc_widget = self.clip_data_bottom.create_preview_widget(max_height=60)
        self.desc_widget.setTextFormat(Qt.MarkdownText)
        self.desc_widget.setObjectName("manual_card_bottom")
        text_col.addWidget(self.title_widget)
        text_col.addWidget(self.desc_widget)

        # edit button on the far right
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(EDIT_ICON_LIGHT)
        self.edit_btn.setIconSize(icon_size)
        self.edit_btn.setToolTip("Edit")
        self.edit_btn.setAutoRaise(True)

        layout.addLayout(icon_col)
        layout.addLayout(text_col)
        layout.addWidget(self.edit_btn, alignment=Qt.AlignTop)

    def _setup_styles(self) -> None:
        self.setStyleSheet(
            """
            QFrame#manual_card {
                border: 1px solid #ccc;
                background-color: #ffffff;
                border-radius: 10px;
                padding: 5px;
                padding-bottom: 10px;
            }
            QFrame#manual_card:hover {
                border: 2px solid #2979ff;
            }
            QLabel#manual_card_top {
                color: #7a7a7a;
                font-size: 7pt;
            }
            QLabel#manual_card_bottom {
                color: #111111;
                font-size: 10pt;
            }
            QToolButton {
                background: transparent;
                border: none;
            }
            QToolButton:hover {
                background: #e0e0e0;
                border-radius: 4px;
            }
            QToolButton#placeholder:hover {
                background: none;
            }
            QLabel {
                border: none;
                color: black;
                font-size: 10pt;
                padding: 0px;
                margin: 0px;
                background-color: transparent;
            }
            
            """
        )

    def _connect_signals(self) -> None:
        # Use partials or instance methods to avoid late-binding issues in loops
        self.copy_btn.clicked.connect(partial(self._on_copy_clicked))
        self.delete_btn.clicked.connect(partial(self._on_delete_clicked))
        self.edit_btn.clicked.connect(partial(self._on_edit_clicked))

        # If you want clicking the labels to paste:
        self.title_widget.mousePressEvent = lambda event: self._on_label_clicked(event, self.clip_data_top.mime_data)
        self.desc_widget.mousePressEvent = lambda event: self._on_label_clicked(event, self.clip_data_bottom.mime_data)
    
    def toggle_delete(self, visible: bool):
        self.delete_btn.setVisible(visible)
        self.delete_button_placeholder.setVisible(not visible)

    def _on_copy_clicked(self):
        self.copyRequested.emit(self.clip_data_bottom.mime_data)

    def _on_delete_clicked(self):
        self.deleteRequested.emit(self.id)

    def _on_edit_clicked(self):
        self.editRequested.emit(self.id)

    def _on_label_clicked(self, event, mime_data):
        if event.button() == Qt.LeftButton:
            self.pasteRequested.emit(mime_data)

    def update_texts(self, top_text: Optional[str] = None, bottom_text: Optional[str] = None):
        if top_text is not None:
            self.top_text = top_text
            self.top_label.setText(top_text)
            self.top_label.setToolTip(top_text)
        if bottom_text is not None:
            self.bottom_text = bottom_text
            self.bottom_label.setText(bottom_text)
