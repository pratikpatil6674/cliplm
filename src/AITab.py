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
    QComboBox,
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, Signal, QUrl
from pathlib import Path

from resources import *
from FavoriteCard import FavoriteCard
from PromptsStore import PromptsStore

class AITab(QWidget):
    def __init__(self, prompt_store: PromptsStore | None = None):
        super().__init__()
        self.prompt_store = prompt_store
        self.prompt_config = prompt_store.prompt_config if prompt_store else None
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        #open prompts.toml
        self.open_prompts_store_button = QPushButton("Open prompts.toml")
        self.open_prompts_store_button.clicked.connect(self._open_prompts_toml)
        self.layout.addWidget(self.open_prompts_store_button)

        self.ai_checkbox = QCheckBox("Use AI?")
        self.ai_checkbox.setStyleSheet("font-size: 16px; font-family: Ubuntu, sans-serif;")
        self.layout.addWidget(self.ai_checkbox)

        self.label_prompt = QLabel("Select prompt:")
        self.prompt_combo = QComboBox()
        self.prompt_combo.setEditable(False)              # set True to allow typing
        self.prompt_combo.setInsertPolicy(QComboBox.NoInsert)

        # Populate prompt combo with options from prompt_config
        if self.prompt_config:
            for key in self.prompt_config.keys():
                self.prompt_combo.addItem(key)

        self.layout.addWidget(self.label_prompt)
        self.layout.addWidget(self.prompt_combo)

        # Input prompt
        self.ai_input_prompt = QTextEdit()
        self.ai_input_prompt.setFixedHeight(100)
        self.layout.addWidget(self.ai_input_prompt)
        
        # Input data text or image
        self.input_data_label = QTextEdit()
        self.input_data_label.setFixedHeight(100)
        self.layout.addWidget(self.input_data_label)
        
        # AI text output
        self.ai_output_text = QLabel("AI Output")
        self.ai_output_text.setTextFormat(Qt.MarkdownText)
        self.ai_output_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ai_output_text.setWordWrap(True)
        self.ai_output_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.ai_output_text)
        self.layout.addWidget(scroll)
        
        self.setLayout(self.layout)
    
    def _open_prompts_toml(self):
        if self.prompt_store:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.prompt_store.store_path).parent)))
            self.prompt_store.load_prompts()
    
    def _setup_styles(self):
        self.ai_input_prompt.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; margin: 10px;") 
        self.input_data_label.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; margin: 10px; border: 1px solid #ccc;") 
        self.ai_output_text.setStyleSheet("background-color: #ffffff; color: #000000; font-size: 15px; font-family: Ubuntu, sans-serif; padding: 10px; margin: 10px; border: 1px solid #ccc;") 

    def is_ai_enabled(self):
        return self.ai_checkbox.isChecked()
    
    def get_selected_prompt(self):
        prompt_name = self.prompt_combo.currentText()
        return self.prompt_config.get(prompt_name, {}).get('prompt', '')
    
    def set_prompt(self, prompt):
        self.ai_input_prompt.setText(prompt)
    
    def set_input_data(self, input_data):
        self.input_data_label.setText(input_data)
    
    def set_ai_output(self, ai_output_text):
        self.ai_output_text.setText(ai_output_text)