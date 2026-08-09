from copy import deepcopy

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
)


class PromptEditorDialog(QDialog):
    def __init__(
        self,
        prompt_config: dict,
        parent=None,
        editing_prompt_name: str | None = None,
    ):
        super().__init__(parent)
        self.prompt_config = deepcopy(prompt_config)
        self.editing_prompt_name = editing_prompt_name
        self.setObjectName("prompt_editor_dialog")
        self.current_prompt_name = None
        self._setup_ui()
        if editing_prompt_name in self.prompt_config:
            prompt_data = self.prompt_config[editing_prompt_name]
            self.current_prompt_name = editing_prompt_name
            self.name_input.setText(editing_prompt_name)
            self.prompt_input.setPlainText(prompt_data.get("prompt", ""))
        else:
            self._start_new_prompt()

    def _setup_ui(self):
        self.setWindowTitle("Edit prompt" if self.editing_prompt_name else "Add prompt")
        self.resize(560, 420)

        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(14, 14, 14, 14)

        editor = QFrame()
        editor.setObjectName("card")
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(18, 16, 18, 16)
        editor_layout.setSpacing(10)

        name_label = QLabel("Name")
        name_label.setObjectName("field_label")
        editor_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setObjectName("name_input")
        self.name_input.setPlaceholderText("Enter prompt name")
        editor_layout.addWidget(self.name_input)

        prompt_label = QLabel("Prompt")
        prompt_label.setObjectName("field_label")
        editor_layout.addWidget(prompt_label)

        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setObjectName("prompt_input")
        self.prompt_input.setPlaceholderText("Enter prompt instructions")
        editor_layout.addWidget(self.prompt_input, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch(1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondary_button")
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_button)

        save_text = "Save changes" if self.editing_prompt_name else "Add prompt"
        self.save_button = QPushButton(save_text)
        self.save_button.setObjectName("primary_button")
        self.save_button.clicked.connect(self._save_and_accept)
        button_row.addWidget(self.save_button)

        editor_layout.addLayout(button_row)
        root.addWidget(editor, 1)

    def _setup_styles(self):
        self.setStyleSheet(
            """
        QDialog, QWidget {
            background: #f5f7fb;
            color: #1f2933;
        }
        QFrame#sidebar, QFrame#card {
            background: #ffffff;
            border-radius: 10px;
            border: 1px solid rgba(30,36,44,0.06);
        }
        QLabel#section_label {
            border: none;
            background: transparent;
            padding: 0;
            font-size: 14px;
            font-weight: 700;
            color: #52606d;
        }
        QLabel#field_label {
            border: none;
            background: transparent;
            padding: 0;
            font-size: 13px;
            font-weight: 600;
            color: #52606d;
        }
        QListWidget#prompts_list {
            border: 1px solid rgba(30,36,44,0.06);
            border-radius: 8px;
            background: #fbfdff;
            padding: 4px;
            outline: none;
        }
        QListWidget#prompts_list::item {
            padding: 6px 8px;
            border-radius: 6px;
            margin: 1px 0;
        }
        QListWidget#prompts_list::item:selected {
            background: #d9e8ff;
            color: #163a70;
        }
        QLineEdit#name_input, QPlainTextEdit#prompt_input {
            color: #263238;
            border: 1px solid rgba(30,36,44,0.08);
            padding: 8px 10px;
            background: #fbfdff;
            border-radius: 8px;
            font-size: 12pt;
        }
        QLineEdit#name_input:focus, QPlainTextEdit#prompt_input:focus {
            border: 1px solid #3a7ef7;
            background: #ffffff;
        }
        QPushButton#primary_button {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
            font-size: 12pt;
        }
        QPushButton#primary_button:hover {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
        }
        QPushButton#secondary_button {
            background: #ffffff;
            color: #2c62d6;
            border: 1px solid rgba(44,98,214,0.18);
            padding: 6px 12px;
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
            font-size: 12pt;
        }
        QPushButton#secondary_button:hover {
            background: #f0f5ff;
        }
        QPushButton#danger_button {
            background: #ffffff;
            color: #c62828;
            border: 1px solid rgba(198,40,40,0.18);
            padding: 6px 12px;
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
            font-size: 12pt;
        }
        QPushButton#danger_button:hover {
            background: #fff3f3;
        }
        QMessageBox {
            background: #f5f7fb;
        }
        QMessageBox QLabel {
            color: #1f2933;
            font-size: 12pt;
            background: transparent;
        }
        QMessageBox QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
            color: #fff;
            border: none;
            padding: 6px 12px;
            border-radius: 8px;
            text-transform: none;
            font-weight: 600;
            font-size: 12pt;
        }
        """
        )

    def _start_new_prompt(self):
        self.current_prompt_name = None
        self.name_input.clear()
        self.prompt_input.clear()
        self.name_input.setFocus()

    def _normalize_prompt_name(self, prompt_name: str) -> str:
        return " ".join(prompt_name.split()).casefold()

    def _apply_current_prompt(self):
        prompt_name = self.name_input.text().strip()
        prompt_text = self.prompt_input.toPlainText().strip()

        if not prompt_name:
            self._show_error("Prompt Error", "Prompt name cannot be empty.")
            return False

        normalized_name = self._normalize_prompt_name(prompt_name)
        for existing_name in list(self.prompt_config.keys()):
            if existing_name == self.current_prompt_name:
                continue
            if self._normalize_prompt_name(existing_name) == normalized_name:
                self._show_error(
                    "Duplicate Prompt",
                    f"A prompt named '{existing_name}' already exists.",
                )
                return False

        if self.current_prompt_name and self.current_prompt_name in self.prompt_config:
            del self.prompt_config[self.current_prompt_name]

        self.prompt_config[prompt_name] = {"prompt": prompt_text}
        self.current_prompt_name = prompt_name
        return True

    def _save_and_accept(self):
        if not self._apply_current_prompt():
            return
        self.accept()

    def _show_error(self, title: str, message: str):
        self._show_message_box(
            title=title,
            text=message,
            icon=QMessageBox.Critical,
            buttons=QMessageBox.Ok,
            default_button=QMessageBox.Ok,
        )

    def _show_message_box(self, title: str, text: str, icon, buttons, default_button):
        message_box = QMessageBox(self)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.setIcon(icon)
        message_box.setStandardButtons(buttons)
        message_box.setDefaultButton(default_button)
        self._style_message_box_buttons(message_box)
        return message_box.exec()

    def _style_message_box_buttons(self, message_box: QMessageBox):
        primary_roles = {
            QMessageBox.AcceptRole,
            QMessageBox.YesRole,
            QMessageBox.ApplyRole,
        }
        destructive_roles = {
            QMessageBox.DestructiveRole,
        }

        for button in message_box.buttons():
            role = message_box.buttonRole(button)
            if role in destructive_roles:
                button.setProperty("role", "danger")
            elif role in primary_roles:
                button.setProperty("role", "primary")
            else:
                button.setProperty("role", "secondary")

    def _primary_button_stylesheet(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                padding: 6px 12px;
                border-radius: 8px;
                text-transform: none;
                font-weight: 600;
                font-size: 14pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
        """

    def _secondary_button_stylesheet(self):
        return """
            QPushButton {
                background: #ffffff;
                color: #2c62d6;
                border: 1px solid rgba(44,98,214,0.18);
                padding: 6px 12px;
                border-radius: 8px;
                text-transform: none;
                font-weight: 600;
                font-size: 14pt;
            }
            QPushButton:hover {
                background: #f0f5ff;
            }
        """

    def _danger_button_stylesheet(self):
        return """
            QPushButton {
                background: #ffffff;
                color: #c62828;
                border: 1px solid rgba(198,40,40,0.18);
                padding: 6px 12px;
                border-radius: 8px;
                text-transform: none;
                font-weight: 600;
                font-size: 14pt;
            }
            QPushButton:hover {
                background: #fff3f3;
            }
        """

    def _message_box_stylesheet(self):
        return """
            QMessageBox {
                background: #f5f7fb;
            }
            QMessageBox QLabel {
                color: #1f2933;
                font-size: 14pt;
                background: transparent;
            }
        """

    def get_prompt_config(self):
        return deepcopy(self.prompt_config)

    def get_saved_prompt_name(self):
        return self.current_prompt_name
