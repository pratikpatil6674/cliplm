from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
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

from ui.dialogs.llm_profile import LLMProfileManagerDialog
from storage.llm_profiles import normalize_ai_settings
from ui.theme.manager import THEME_OPTIONS


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

        profile_row = QHBoxLayout()
        profile_row.setSpacing(10)
        profile_label = QLabel("Default LLM profile")
        profile_label.setObjectName("field_label")
        profile_row.addWidget(profile_label)

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("text_input")
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.currentIndexChanged.connect(
            self._update_profile_summary
        )
        profile_row.addWidget(self.profile_combo, 1)

        self.manage_profiles_button = QPushButton("Manage")
        self.manage_profiles_button.setObjectName("manage_profiles_button")
        self.manage_profiles_button.setCursor(Qt.PointingHandCursor)
        self.manage_profiles_button.clicked.connect(self._manage_profiles)
        profile_row.addWidget(self.manage_profiles_button)
        ai_layout.addLayout(profile_row)

        self.profile_summary = QFrame()
        self.profile_summary.setObjectName("llm_profile_summary")
        summary_layout = QGridLayout(self.profile_summary)
        summary_layout.setContentsMargins(10, 8, 10, 8)
        summary_layout.setHorizontalSpacing(10)
        summary_layout.setVerticalSpacing(3)
        summary_layout.setColumnMinimumWidth(0, 58)
        summary_layout.setColumnStretch(1, 1)

        endpoint_caption = QLabel("Endpoint")
        endpoint_caption.setObjectName("profile_summary_caption")
        model_caption = QLabel("Model")
        model_caption.setObjectName("profile_summary_caption")
        key_caption = QLabel("API key")
        key_caption.setObjectName("profile_summary_caption")
        self.profile_endpoint_value = QLabel()
        self.profile_endpoint_value.setObjectName("profile_summary_value")
        self.profile_endpoint_value.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )
        self.profile_model_value = QLabel()
        self.profile_model_value.setObjectName("profile_summary_value")
        self.profile_model_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.profile_key_value = QLabel()
        self.profile_key_value.setObjectName("profile_summary_value")
        summary_layout.addWidget(endpoint_caption, 0, 0)
        summary_layout.addWidget(self.profile_endpoint_value, 0, 1)
        summary_layout.addWidget(model_caption, 1, 0)
        summary_layout.addWidget(self.profile_model_value, 1, 1)
        summary_layout.addWidget(key_caption, 2, 0)
        summary_layout.addWidget(self.profile_key_value, 2, 1)
        ai_layout.addWidget(self.profile_summary)

        self._profiles = []

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
            "If you select LLM API, Translate uses the default LLM profile from AI Settings."
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

    def _manage_profiles(self) -> None:
        active_profile_id = self.profile_combo.currentData() or ""
        dialog = LLMProfileManagerDialog(self._profiles, self)
        if dialog.exec() != QDialog.Accepted:
            return

        self._profiles = dialog.profiles()
        profile_ids = {profile["id"] for profile in self._profiles}
        if active_profile_id not in profile_ids:
            active_profile_id = self._profiles[0]["id"] if self._profiles else ""
        self._refresh_profile_combo(active_profile_id)

    def _refresh_profile_combo(self, active_profile_id: str = "") -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in self._profiles:
            self.profile_combo.addItem(profile["name"], profile["id"])

        active_index = self.profile_combo.findData(active_profile_id)
        if active_index < 0 and self.profile_combo.count():
            active_index = 0
        self.profile_combo.setCurrentIndex(active_index)
        self.profile_combo.setEnabled(bool(self._profiles))
        self.profile_combo.blockSignals(False)
        self._update_profile_summary()

    def _update_profile_summary(self, *_args) -> None:
        profile_id = self.profile_combo.currentData()
        profile = next(
            (
                profile
                for profile in self._profiles
                if profile["id"] == profile_id
            ),
            None,
        )
        if profile is None:
            self.profile_endpoint_value.setText("No profiles configured")
            self.profile_model_value.setText("Add a profile to enable AI features")
            self.profile_key_value.setText("Not configured")
            return

        self.profile_endpoint_value.setText(profile["endpoint"])
        self.profile_endpoint_value.setToolTip(profile["endpoint"])
        self.profile_model_value.setText(profile["model"])
        self.profile_key_value.setText(
            "Saved" if profile["api_key"] else "Not required"
        )

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
        ai_settings = normalize_ai_settings(settings.get("ai", {}))
        translate_settings = settings.get("translate", {})
        theme_index = self.theme_combo.findData(
            appearance_settings.get("theme", "blue")
        )
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.dark_mode_checkbox.setChecked(
            appearance_settings.get("dark_mode", False)
        )
        self._profiles = ai_settings["profiles"]
        self._refresh_profile_combo(ai_settings["active_profile_id"])
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
                "active_profile_id": self.profile_combo.currentData() or "",
                "profiles": self._profiles,
            },
            "translate": {
                "enabled": self.translate_enabled_checkbox.isChecked(),
                "api": self.translate_api_combo.currentData(),
            },
        }
