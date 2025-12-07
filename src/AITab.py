from typing import Container
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
    QFrame
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtCore import Qt, Signal, QUrl
from pathlib import Path

from resources import *
from FavoriteCard import FavoriteCard
from PromptsStore import PromptsStore
from PlaceHolder import Placeholder

class AITab(QWidget):
    def __init__(self, prompt_store: PromptsStore | None = None):
        super().__init__()
        self.prompt_store = prompt_store
        self.prompt_config = prompt_store.prompt_config if prompt_store else None
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        
        root = QVBoxLayout(self)
        root.setSpacing(5)
        root.setContentsMargins(10, 10, 10, 10)

        # ---- AI toggle ----
        self.ai_checkbox = QCheckBox("Use AI?")
        self.ai_checkbox.setObjectName("ai_checkbox")
        self.ai_checkbox.setStyleSheet("font-size: 12px; font-family: Ubuntu, sans-serif;")
        # ---- AI toggle ----

        # ---- Prompt selection ----
        self.prompt_combo = QComboBox()
        self.prompt_combo.setObjectName("prompt_combo")
        self.prompt_combo.setPlaceholderText("Select prompt")
        self.prompt_combo.setEditable(False)              # set True to allow typing
        self.prompt_combo.setInsertPolicy(QComboBox.NoInsert)

        if self.prompt_config:
            for key in self.prompt_config.keys():
                self.prompt_combo.addItem(key)
        # ---- Prompt selection ----
        
        # ---- Button open prompts.toml ----
        self.open_prompts_store_button = QPushButton("Edit Prompts")
        self.open_prompts_store_button.setObjectName("open_prompts_store_button")
        self.open_prompts_store_button.clicked.connect(self._open_prompts_toml)
        self.open_prompts_store_button.setCursor(Qt.PointingHandCursor)
        # ---- Button open prompts.toml ----
        
        # ---- Top row layout ----
        # top_row_container = QFrame()
        # top_row_container.setObjectName("top_row_container")
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self.ai_checkbox, 0, Qt.AlignVCenter)
        top_row.addStretch(1)
        top_row.addWidget(self.prompt_combo, 0)
        top_row.addSpacing(8)
        top_row.addWidget(self.open_prompts_store_button, 0)

        root.addLayout(top_row)
        # ---- Top row layout ----
    
        # Card for prompt, output
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(8)
        
        # ---- Input prompt ----
        self.ai_input_prompt = QLabel()
        self.ai_input_prompt.setObjectName("ai_input_prompt")
        self.ai_input_prompt.setTextFormat(Qt.PlainText)
        self.ai_input_prompt.setWordWrap(True)
        card_layout.addWidget(self.ai_input_prompt)
        # ---- Input prompt ----

        # ---- Input data text or image ----
        self.input_data_placeholder = Placeholder(self)
        self.input_data_placeholder.setObjectName("input_data_placeholder")
        scroll1 = QScrollArea()
        scroll1.setWidgetResizable(True)
        scroll1.setWidget(self.input_data_placeholder)
        card_layout.addWidget(scroll1)
        # ---- Input data text or image ----
        
        # ---- AI text output ----
        self.ai_output_text = QLabel("AI Output")
        self.ai_output_text.setObjectName("ai_output_text")
        self.ai_output_text.setTextFormat(Qt.MarkdownText)
        self.ai_output_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ai_output_text.setWordWrap(True)
        self.ai_output_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)

        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setWidget(self.ai_output_text)
        card_layout.addWidget(scroll2)
        # ---- AI text output ----

        root.addWidget(card)
    
        # Set the main layout to the container
        self.setLayout(root)
    
    def _open_prompts_toml(self):
        if self.prompt_store:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.prompt_store.store_path).parent)))
            self.prompt_store.load_prompts()
    
    def _setup_styles(self):
        self.setStyleSheet("""
        /* overall */
        QWidget { background: #f5f7fb; color: #1f2933; }

        /* Primary button */
        QPushButton#open_prompts_store_button {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 600;
            min-width: 110px;
            text-transform: none; 
            font-family: Ubuntu, sans-serif;
            font-size: 15px;
        }
        QPushButton#open_prompts_store_button:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0); }
        QPushButton#open_prompts_store_button:pressed { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2f66d0, stop:1 #264fb0); }

        /* Combo box */
        QComboBox#prompt_combo {
            padding: 6px 10px;
            min-height: 30px;
            border-radius: 8px;
            border: 1px solid rgba(20,24,30,0.06);
            background: white;
            font-size: 13px;
        }
        QComboBox#prompt_combo::drop-down { width: 30px; subcontrol-origin: padding; subcontrol-position: top right; border-left: 1px solid rgba(0,0,0,0.04); }

        /* Card and output */
        QFrame#card {
            background: #ffffff;
            border-radius: 10px;
            border: 1px solid rgba(30,36,44,0.06);
            padding: 10px;
        }
        QLabel { 
            color: #263238; margin: 0;
            border: 1px solid rgba(30,36,44,0.06);
            padding: 8px;
            background: #fbfdff;
            border-radius: 8px;
        }
        """)
        self.input_data_placeholder.setStyleSheet("""
            font-weight: 700; color: #263238; margin: 0;
            border: 1px solid rgba(30,36,44,0.06);
            padding: 8px;
            background: #fbfdff;
            border-radius: 8px;
        """)

    def is_ai_enabled(self):
        return self.ai_checkbox.isChecked()
    
    def get_selected_prompt(self):
        prompt_name = self.prompt_combo.currentText()
        return self.prompt_config.get(prompt_name, {}).get('prompt', '')
    
    def set_prompt(self, prompt):
        self.ai_input_prompt.setText(prompt)
    
    def set_input_data(self, input_data_widget):
        self.input_data_placeholder.set_widget(input_data_widget)
    
    def set_ai_output(self, ai_output_text):
        self.ai_output_text.setText(ai_output_text)