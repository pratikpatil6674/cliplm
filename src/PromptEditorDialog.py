from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PromptEditorDialog(QDialog):
    def __init__(self, prompt_config: dict, parent=None):
        super().__init__(parent)
        self.prompt_config = deepcopy(prompt_config)
        self.current_prompt_name = None
        self._setup_ui()
        self._setup_styles()
        self._populate_prompt_list()
        self._start_new_prompt()

    def _setup_ui(self):
        self.setWindowTitle("Edit prompts")
        self.resize(760, 520)

        root = QHBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(10, 10, 10, 10)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        prompts_label = QLabel("Prompts")
        prompts_label.setObjectName("section_label")
        sidebar_layout.addWidget(prompts_label)

        self.prompts_list = QListWidget()
        self.prompts_list.setObjectName("prompts_list")
        self.prompts_list.currentItemChanged.connect(self._load_selected_prompt)
        sidebar_layout.addWidget(self.prompts_list, 1)

        self.new_button = QPushButton("New prompt")
        self.new_button.setObjectName("secondary_button")
        self.new_button.clicked.connect(self._start_new_prompt)
        sidebar_layout.addWidget(self.new_button)

        self.delete_button = QPushButton("Delete prompt")
        self.delete_button.setObjectName("danger_button")
        self.delete_button.clicked.connect(self._delete_current_prompt)
        sidebar_layout.addWidget(self.delete_button)

        root.addWidget(sidebar)

        editor = QFrame()
        editor.setObjectName("card")
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(10, 10, 10, 10)
        editor_layout.setSpacing(8)

        title_label = QLabel("Prompt details")
        title_label.setObjectName("section_label")
        editor_layout.addWidget(title_label)

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

        self.apply_button = QPushButton("Apply")
        self.apply_button.setObjectName("secondary_button")
        self.apply_button.clicked.connect(self._apply_current_prompt)
        button_row.addWidget(self.apply_button)

        self.save_button = QPushButton("Save prompts")
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

    def _populate_prompt_list(self):
        self.prompts_list.clear()
        for prompt_name in self.prompt_config.keys():
            self.prompts_list.addItem(QListWidgetItem(prompt_name))

        if self.prompts_list.count() > 0:
            self.prompts_list.setCurrentRow(0)

    def _start_new_prompt(self):
        self.current_prompt_name = None
        self.prompts_list.clearSelection()
        self.name_input.clear()
        self.prompt_input.clear()
        self.name_input.setFocus()
        self._update_delete_button_state()

    def _load_selected_prompt(self, item: QListWidgetItem, previous: QListWidgetItem | None = None):
        if item is None:
            self.current_prompt_name = None
            self._update_delete_button_state()
            return
        prompt_name = item.text()
        prompt_data = self.prompt_config.get(prompt_name, {})
        self.current_prompt_name = prompt_name
        self.name_input.setText(prompt_name)
        self.prompt_input.setPlainText(prompt_data.get("prompt", ""))
        self._update_delete_button_state()

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
        self._populate_prompt_list()
        self._select_prompt(prompt_name)
        return True

    def _select_prompt(self, prompt_name: str):
        matches = self.prompts_list.findItems(prompt_name, Qt.MatchExactly)
        if matches:
            self.prompts_list.setCurrentItem(matches[0])

    def _save_and_accept(self):
        if not self._apply_current_prompt():
            return
        self.accept()

    def _delete_current_prompt(self):
        if not self.current_prompt_name:
            return

        prompt_name = self.current_prompt_name
        answer = self._show_message_box(
            title="Delete Prompt",
            text=f"Delete '{prompt_name}'?",
            icon=QMessageBox.Warning,
            buttons=QMessageBox.Yes | QMessageBox.No,
            default_button=QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.prompt_config.pop(prompt_name, None)
        self._populate_prompt_list()
        if self.prompts_list.count() > 0:
            self.prompts_list.setCurrentRow(0)
        else:
            self._start_new_prompt()

    def _update_delete_button_state(self):
        self.delete_button.setEnabled(bool(self.current_prompt_name))

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
        message_box.setStyleSheet(self._message_box_stylesheet())
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
                button.setStyleSheet(self._danger_button_stylesheet())
            elif role in primary_roles:
                button.setStyleSheet(self._primary_button_stylesheet())
            else:
                button.setStyleSheet(self._secondary_button_stylesheet())

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
