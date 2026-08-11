from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ThemeManager import THEME_OPTIONS


class SettingsTab(QWidget):
    saveRequested = Signal()

    def __init__(self, config_dir="", data_dir="", cache_dir=""):
        super().__init__()
        self._storage_directories = (
            ("Config", config_dir),
            ("Data", data_dir),
            ("Cache", cache_dir),
        )
        self.setObjectName("settings_tab")
        self._setup_ui()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("settings_scroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("settings_content")
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 14, 16, 14)

        appearance_card = QFrame()
        appearance_card.setObjectName("card")
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setSpacing(10)
        appearance_layout.setContentsMargins(16, 14, 16, 14)

        appearance_title = QLabel("Appearance")
        appearance_title.setObjectName("settings_card_title")
        appearance_layout.addWidget(appearance_title)

        appearance_options = QHBoxLayout()
        appearance_options.setSpacing(14)
        self.theme_label = QLabel("Accent")
        self.theme_label.setObjectName("field_label")
        appearance_options.addWidget(self.theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("text_input")
        for label, value in THEME_OPTIONS:
            self.theme_combo.addItem(label, value)
        appearance_options.addWidget(self.theme_combo, 1)

        self.dark_mode_checkbox = QCheckBox("Dark mode")
        self.dark_mode_checkbox.setObjectName("toggle")
        appearance_options.addWidget(self.dark_mode_checkbox)
        appearance_layout.addLayout(appearance_options)
        layout.addWidget(appearance_card)
        ai_card = QFrame()
        ai_card.setObjectName("card")
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setSpacing(8)
        ai_layout.setContentsMargins(16, 14, 16, 14)

        ai_title = QLabel("AI Settings")
        ai_title.setObjectName("settings_card_title")
        ai_layout.addWidget(ai_title)
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(10)
        form_layout.setColumnMinimumWidth(0, 190)
        form_layout.setColumnStretch(1, 1)


        self.endpoint_label = QLabel("OpenAI Compatible Endpoint")
        self.endpoint_label.setObjectName("field_label")

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setObjectName("text_input")
        self.endpoint_input.setPlaceholderText("https://api.example.com/v1/")
        form_layout.addWidget(self.endpoint_input, 0, 1)

        self.model_label = QLabel("Model")
        self.model_label.setObjectName("field_label")

        self.model_input = QLineEdit()
        self.model_input.setObjectName("text_input")
        self.model_input.setPlaceholderText("gpt-4.1-mini")
        form_layout.addWidget(self.model_input, 1, 1)

        self.api_key_label = QLabel("API Key")
        self.api_key_label.setObjectName("field_label")

        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("text_input")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API key")
        form_layout.addWidget(self.endpoint_label, 0, 0)
        form_layout.addWidget(self.model_label, 1, 0)
        form_layout.addWidget(self.api_key_label, 2, 0)
        form_layout.addWidget(self.api_key_input, 2, 1)
        ai_layout.addLayout(form_layout)

        layout.addWidget(ai_card)

        translate_card = QFrame()
        translate_card.setObjectName("card")
        translate_layout = QVBoxLayout(translate_card)
        translate_layout.setSpacing(8)
        translate_layout.setContentsMargins(16, 14, 16, 14)

        translate_title = QLabel("Translate Settings")
        translate_title.setObjectName("settings_card_title")
        translate_layout.addWidget(translate_title)

        self.translate_enabled_checkbox = QCheckBox("Enable Translate tab")
        self.translate_enabled_checkbox.setObjectName("toggle")

        self.translate_api_label = QLabel("Translation API")
        self.translate_api_label.setObjectName("field_label")

        self.translate_api_combo = QComboBox()
        self.translate_api_combo.setObjectName("text_input")
        self.translate_api_combo.addItem("Google Translate API", "google")
        self.translate_api_combo.addItem("LLM API", "llm")

        translate_options = QHBoxLayout()
        translate_options.setSpacing(14)
        translate_options.addWidget(self.translate_enabled_checkbox)
        translate_options.addStretch(1)
        translate_options.addWidget(self.translate_api_label)
        translate_options.addWidget(self.translate_api_combo, 1)
        translate_layout.addLayout(translate_options)

        translate_hint = QLabel(
            "Source and target language preferences are saved from the Translate tab. "
            "If you select LLM API, Translate uses the endpoint, model, and API key from AI Settings."
        )
        translate_hint.setObjectName("hint_label")
        translate_hint.setWordWrap(True)
        translate_layout.addWidget(translate_hint)

        layout.addWidget(translate_card)

        storage_card = QFrame()
        storage_card.setObjectName("card")
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setSpacing(8)
        storage_layout.setContentsMargins(16, 12, 16, 12)

        storage_title = QLabel("Storage locations")
        storage_title.setObjectName("settings_card_title")
        storage_layout.addWidget(storage_title)

        directory_grid = QGridLayout()
        directory_grid.setHorizontalSpacing(8)
        directory_grid.setVerticalSpacing(6)
        directory_grid.setColumnMinimumWidth(0, 54)
        directory_grid.setColumnStretch(1, 1)
        self.directory_inputs = {}

        for row, (name, path) in enumerate(self._storage_directories):
            label = QLabel(name)
            label.setObjectName("field_label")

            path_input = QLineEdit(str(path))
            path_input.setObjectName("directory_path")
            path_input.setReadOnly(True)
            path_input.setToolTip(str(path))
            path_input.setCursorPosition(0)
            self.directory_inputs[name.lower()] = path_input

            open_button = QPushButton("Open")
            open_button.setObjectName("directory_open_button")
            open_button.setCursor(Qt.PointingHandCursor)
            open_button.setFixedSize(62, 30)
            open_button.setEnabled(bool(path))
            open_button.clicked.connect(
                lambda _checked=False, directory=path: self._open_directory(
                    directory
                )
            )

            directory_grid.addWidget(label, row, 0)
            directory_grid.addWidget(path_input, row, 1)
            directory_grid.addWidget(open_button, row, 2)

        storage_layout.addLayout(directory_grid)
        layout.addWidget(storage_card)
        layout.addStretch(1)

        scroll_area.setWidget(content)
        root_layout.addWidget(scroll_area, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 6, 16, 14)
        footer.addStretch(1)

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("save_button")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.saveRequested.emit)
        footer.addWidget(self.save_button)

        root_layout.addLayout(footer)

    @staticmethod
    def _open_directory(path) -> None:
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _setup_styles(self):
        self.setStyleSheet(
            """
            QWidget { background: #f5f7fb; color: #1f2933; }
            QFrame#card {
                background: #ffffff;
                border-radius: 12px;
                border: 1px solid rgba(30,36,44,0.08);
            }
            QLabel#settings_card_title {
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
        appearance_settings = settings.get("appearance", {})
        ai_settings = settings.get("ai", {})
        translate_settings = settings.get("translate", {})
        theme_index = self.theme_combo.findData(
            appearance_settings.get("theme", "blue")
        )
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.dark_mode_checkbox.setChecked(
            appearance_settings.get("dark_mode", False)
        )
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
            "appearance": {
                "theme": self.theme_combo.currentData(),
                "dark_mode": self.dark_mode_checkbox.isChecked(),
            },
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
