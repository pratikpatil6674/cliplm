from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Qt, Signal, QMimeData
from functools import partial
import sys
from resources import *

class FavoriteCard(QFrame):
    copyRequested = Signal(QMimeData)
    pasteRequested = Signal(QMimeData)
    deleteRequested = Signal(str)
    def __init__(self, id, clip_data):
        super().__init__()
        
        self.id = id
        self.clip_data = clip_data

        self._setup_ui()
        self._setup_styles()
        self._connect_signals()
    
    def toggle_delete(self, visible: bool):
        self.delete_button.setVisible(visible)
        self.delete_button_placeholder.setVisible(not visible)
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(60)
        self.setMaximumHeight(180)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        
        # Left: Vertical button layout
        btn_size = 15
        btn_layout = QVBoxLayout()
        btn_layout.addStretch()

        # btn_layout.setSpacing(0)
        # btn_layout.setContentsMargins(0, 0, 0, 0)
        self.copy_button = QPushButton()
        self.copy_button.setIcon(COPY_ICON)
        self.copy_button.setFixedSize(btn_size, btn_size)
        btn_layout.addWidget(self.copy_button)

        btn_layout.addStretch()

        self.delete_button = QPushButton()
        self.delete_button.setIcon(DELETE_ICON)
        self.delete_button.setFixedSize(btn_size, btn_size)
        btn_layout.addWidget(self.delete_button)


        self.delete_button_placeholder = QPushButton()
        self.delete_button_placeholder.setFixedSize(btn_size, btn_size)
        self.delete_button_placeholder.hide()
        btn_layout.addWidget(self.delete_button_placeholder)

        btn_layout.addStretch()

        self.clip_widget = self.clip_data.create_preview_widget(max_height=150)

        # Add both parts to the card layout
        layout.addLayout(btn_layout)
        layout.addWidget(self.clip_widget)
    
    def _setup_styles(self):
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                background-color: #ffffff;
                border-radius: 10px;
            }
            QFrame:hover {
                border: 2px solid #2979ff;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLabel {
                border: none;
                color: black; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 0px; background-color: transparent;
            }
            QLabel:hover {
                border: none;
            }
        """)
        # self.label.setStyleSheet(f"color: black; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 0px; margin: 0px; background-color: transparent;")
    
    def _connect_signals(self) -> None:
        # Use partials or instance methods to avoid late-binding issues in loops
        self.copy_button.clicked.connect(partial(self._on_copy_clicked))
        self.delete_button.clicked.connect(partial(self._on_delete_clicked))
        self.clip_widget.mousePressEvent = lambda event: self._on_label_clicked(event)

    # --- private slots ---
    def _on_copy_clicked(self):
        self.copyRequested.emit(self.clip_data.mime_data)

    def _on_delete_clicked(self):
        self.deleteRequested.emit(self.id)

    def _on_label_clicked(self, event):
        # If you want left click only:
        if event.button() == Qt.LeftButton:
            self.pasteRequested.emit(self.clip_data.mime_data)


class Demo(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()
        main_layout.addWidget(fav_card("Hello World", self.delete_callback, self.copy_callback, self.paste_callback))
        self.setLayout(main_layout)

    def delete_callback(self, card):
        print("Delete clicked")

    def copy_callback(self, text):
        print("Copy clicked", text)

    def paste_callback(self, event, text):
        print("Paste clicked", text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Demo()
    window.resize(400, 100)
    window.show()
    sys.exit(app.exec())
