from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QListWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QListWidgetItem,
    QDialog,
    QCheckBox,
    QScrollArea,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal
import sys
from resources import *
from FavoriteCard import FavoriteCard

class TranslateTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.translate_checkbox = QCheckBox("Translate?")
        self.layout.addWidget(self.translate_checkbox)

        self.translate_src_text = QTextEdit()
        self.translate_src_text.setFixedHeight(200)
        self.layout.addWidget(self.translate_src_text)
        
        self.translated_text = QLabel("Translated Text")
        self.translated_text.setTextFormat(Qt.RichText)
        self.translated_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translated_text.setWordWrap(True)
        self.translated_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.translated_text)

        self.layout.addWidget(scroll)
        
        self.setLayout(self.layout)
    
    def _setup_styles(self):
        self.translate_src_text.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; margin: 10px;") 
        self.translated_text.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; margin: 10px; border: 1px solid #ccc;") 

    def is_translate_enabled(self):
        return self.translate_checkbox.isChecked()
    
    def set_text(self, text, translated_text):
        self.translate_src_text.setText(text)
        self.translated_text.setText(translated_text)
