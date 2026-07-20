from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsTab(QWidget):
    saveRequested = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        ai_card = QFrame()
        ai_card.setObjectName("card")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(8)
        ai_layout.setContentsMargins(12, 12, 12, 12)

        ai_title = QLabel("Agent Settings")
        ai_title.setObjectName("card_title")
        ai_layout.addWidget(ai_title)

        self.endpoint_label = QLabel("OpenAI Compatible Endpoint")
        self.endpoint_label.setObjectName("field_label")
        ai_layout.addWidget(self.endpoint_label)

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setObjectName("text_input")
        self.endpoint_input.setPlaceholderText("https://api.example.com/v1/")
        ai_layout.addWidget(self.endpoint_input)

        self.model_label = QLabel("Model")
        self.model_label.setObjectName("field_label")
        ai_layout.addWidget(self.model_label)

        self.model_input = QLineEdit()
        self.model_input.setObjectName("text_input")
        self.model_input.setPlaceholderText("gpt-4.1-mini")
        ai_layout.addWidget(self.model_input)

        self.api_key_label = QLabel("API Key")
        self.api_key_label.setObjectName("field_label")
        ai_layout.addWidget(self.api_key_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("text_input")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API key")
        ai_layout.addWidget(self.api_key_input)

        layout.addWidget(ai_card)

        translate_card = QFrame()
        translate_card.setObjectName("card")
        translate_layout = QVBoxLayout(translate_card)
        translate_layout.setSpacing(8)
        translate_layout.setContentsMargins(12, 12, 12, 12)

        translate_title = QLabel("Translate Settings")
        translate_title.setObjectName("card_title")
        translate_layout.addWidget(translate_title)

        self.translate_enabled_checkbox = QCheckBox("Enable Translate tab")
        self.translate_enabled_checkbox.setObjectName("toggle")
        translate_layout.addWidget(self.translate_enabled_checkbox)

        self.translate_api_label = QLabel("Translation API")
        self.translate_api_label.setObjectName("field_label")
        translate_layout.addWidget(self.translate_api_label)

        self.translate_api_combo = QComboBox()
        self.translate_api_combo.setObjectName("text_input")
        self.translate_api_combo.addItem("Google Translate API", "google")
        self.translate_api_combo.addItem("LLM API", "llm")
        translate_layout.addWidget(self.translate_api_combo)

        translate_hint = QLabel(
            "Source and target language preferences are saved from the Translate tab. "
            "If you select LLM API, Translate uses the endpoint, model, and API key from Agent Settings."
        )
        translate_hint.setObjectName("hint_label")
        translate_hint.setWordWrap(True)
        translate_layout.addWidget(translate_hint)

        layout.addWidget(translate_card)
        layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("save_button")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.saveRequested.emit)
        footer.addWidget(self.save_button)

        layout.addLayout(footer)

    def _setup_styles(self):
        self.setStyleSheet(
            """
            QWidget { background: #f5f7fb; color: #1f2933; }
            QFrame#card {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid rgba(30,36,44,0.08);
            }
            QLabel#card_title {
                border: none;
                background: transparent;
                padding: 0;
                font-size: 12pt;
                font-weight: 700;
                color: #22303c;
            }
            QLabel#field_label {
                border: none;
                background: transparent;
                padding: 0;
                font-size: 10pt;
                font-weight: 700;
                color: #52606d;
            }
            QLabel#hint_label {
                border: none;
                background: #f8fbff;
                color: #52606d;
                padding: 8px 10px;
                border-radius: 8px;
                font-size: 10pt;
            }
            QLineEdit#text_input {
                background: #fbfdff;
                border: 1px solid rgba(30,36,44,0.10);
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 10pt;
            }
            QPushButton#save_button {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                padding: 8px 10px;
                border-radius: 8px;
                min-width: 60px;
                text-transform: none;
                font-weight: 600;
                font-size: 12pt;
            }
            QPushButton#save_button:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
            QCheckBox#toggle {
                font-size: 10pt;
            }
        """
        )

    def set_settings(self, settings):
        ai_settings = settings.get("ai", {})
        translate_settings = settings.get("translate", {})
        self.endpoint_input.setText(ai_settings.get("endpoint", ""))
        self.model_input.setText(ai_settings.get("model", ""))
        self.api_key_input.setText(ai_settings.get("api_key", ""))
        self.translate_enabled_checkbox.setChecked(
            translate_settings.get("enabled", True)
        )
        translate_api_index = self.translate_api_combo.findData(
            translate_settings.get("api", "google")
        )
        self.translate_api_combo.setCurrentIndex(
            translate_api_index if translate_api_index >= 0 else 0
        )

    def get_settings(self):
        return {
            "ai": {
                "endpoint": self.endpoint_input.text().strip(),
                "model": self.model_input.text().strip(),
                "api_key": self.api_key_input.text().strip(),
            },
            "translate": {
                "enabled": self.translate_enabled_checkbox.isChecked(),
                "api": self.translate_api_combo.currentData(),
            },
        }
