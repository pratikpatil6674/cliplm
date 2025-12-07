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
from PySide6.QtCore import Qt, Signal
from resources import *

class TranslateTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.translate_checkbox = QCheckBox("Translate?")
        self.layout.addWidget(self.translate_checkbox)

        self.translate_src_text = QLabel()
        self.translate_src_text.setFixedHeight(200)
        self.translate_src_text.setTextFormat(Qt.RichText)
        self.translate_src_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translate_src_text.setWordWrap(True)
        self.translate_src_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        scroll1 = QScrollArea()
        scroll1.setWidgetResizable(True)
        scroll1.setWidget(self.translate_src_text)
        self.layout.addWidget(scroll1)
        
        self.translated_text = QLabel("Translated Text")
        self.translated_text.setTextFormat(Qt.RichText)
        self.translated_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translated_text.setWordWrap(True)
        self.translated_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setWidget(self.translated_text)
        self.layout.addWidget(scroll2)
        
    def _setup_styles(self):
        self.setStyleSheet(f"background: #F5F7FB; ")
        common_style = "background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; border: 1px solid #ccc;"
        self.translate_src_text.setStyleSheet(common_style)
        self.translated_text.setStyleSheet(common_style)

    def is_translate_enabled(self):
        return self.translate_checkbox.isChecked()
    
    def set_text(self, text, translated_text):
        self.translate_src_text.setText(text)
        self.translated_text.setText(translated_text)
