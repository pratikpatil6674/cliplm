from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from storage.llm_profiles import (
    LLMProfileValidationError,
    new_profile_id,
    validate_profile,
)


class LLMProfileManagerDialog(QDialog):
    """Stages profile collection changes in a combined list and editor."""

    def __init__(self, profiles: list[dict], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("llm_profile_manager_dialog")
        self.setWindowTitle("Manage LLM profiles")
        self.setModal(True)
        self.resize(700, 350)
        self.setMinimumSize(620, 330)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._profiles = deepcopy(profiles)
        self._loading_profile = False
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        description = QLabel(
            "Select a profile to edit its endpoint, model, and API key. "
            "Changes are saved with the main Settings Save button."
        )
        description.setObjectName("dialog_description")
        description.setWordWrap(True)
        root.addWidget(description)

        content = QHBoxLayout()
        content.setSpacing(8)

        list_column = QVBoxLayout()
        list_column.setSpacing(8)
        self.profile_list = QListWidget()
        self.profile_list.setObjectName("llm_profile_list")
        self.profile_list.setMinimumWidth(155)
        self.profile_list.setMaximumWidth(180)
        self.profile_list.currentItemChanged.connect(
            self._load_selected_profile
        )
        list_column.addWidget(self.profile_list, 1)

        list_actions = QGridLayout()
        list_actions.setHorizontalSpacing(6)
        list_actions.setVerticalSpacing(6)
        add_button = QPushButton("Add")
        add_button.setProperty("role", "primary")
        add_button.clicked.connect(self._add_profile)
        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.clicked.connect(self._duplicate_selected)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setProperty("role", "danger")
        self.delete_button.clicked.connect(self._delete_selected)
        list_actions.addWidget(add_button, 0, 0, 1, 2)
        list_actions.addWidget(self.duplicate_button, 1, 0)
        list_actions.addWidget(self.delete_button, 1, 1)
        list_column.addLayout(list_actions)
        content.addLayout(list_column)

        self.editor_card = QFrame()
        self.editor_card.setObjectName("llm_profile_details")
        editor_layout = QVBoxLayout(self.editor_card)
        editor_layout.setContentsMargins(12, 10, 12, 10)
        editor_layout.setSpacing(7)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setColumnMinimumWidth(0, 78)
        form.setColumnStretch(1, 1)
        self.name_input = self._add_field(
            form, 0, "Profile name", "Work account"
        )
        self.endpoint_input = self._add_field(
            form, 1, "Endpoint URL", "https://api.example.com/v1"
        )
        self.model_input = self._add_field(
            form, 2, "Model", "gpt-4.1-mini"
        )

        api_key_label = QLabel("API key")
        api_key_label.setObjectName("field_label")
        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("text_input")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Optional for local endpoints")
        self.show_key_checkbox = QCheckBox("Show")
        self.show_key_checkbox.setObjectName("toggle")
        self.show_key_checkbox.toggled.connect(
            lambda visible: self.api_key_input.setEchoMode(
                QLineEdit.Normal if visible else QLineEdit.Password
            )
        )
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        key_row.addWidget(self.api_key_input, 1)
        key_row.addWidget(self.show_key_checkbox)
        form.addWidget(api_key_label, 3, 0)
        form.addLayout(key_row, 3, 1)
        editor_layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("validation_error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        editor_layout.addWidget(self.error_label)
        editor_layout.addStretch(1)
        content.addWidget(self.editor_card, 1)
        root.addLayout(content, 1)

        dialog_actions = QHBoxLayout()
        dialog_actions.setSpacing(8)
        hint = QLabel("Profile changes are staged until Settings is saved.")
        hint.setObjectName("dialog_description")
        dialog_actions.addWidget(hint)
        dialog_actions.addStretch(1)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        done_button = QPushButton("Done")
        done_button.setProperty("role", "primary")
        done_button.clicked.connect(self._validate_and_accept)
        dialog_actions.addWidget(cancel_button)
        dialog_actions.addWidget(done_button)
        root.addLayout(dialog_actions)

        for field in (
            self.name_input,
            self.endpoint_input,
            self.model_input,
            self.api_key_input,
        ):
            field.textEdited.connect(self._stage_current_profile)

    @staticmethod
    def _add_field(
        form: QGridLayout,
        row: int,
        label_text: str,
        placeholder: str,
    ) -> QLineEdit:
        label = QLabel(label_text)
        label.setObjectName("field_label")
        field = QLineEdit()
        field.setObjectName("text_input")
        field.setPlaceholderText(placeholder)
        form.addWidget(label, row, 0)
        form.addWidget(field, row, 1)
        return field

    def _refresh_list(self, selected_id: str = "") -> None:
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        selected_item = None
        for profile in self._profiles:
            item = QListWidgetItem(profile["name"] or "Untitled profile")
            item.setData(Qt.UserRole, profile["id"])
            item.setToolTip(profile["endpoint"])
            self.profile_list.addItem(item)
            if profile["id"] == selected_id:
                selected_item = item
        self.profile_list.blockSignals(False)

        if selected_item is not None:
            self.profile_list.setCurrentItem(selected_item)
        elif self.profile_list.count():
            self.profile_list.setCurrentRow(0)
        else:
            self._load_selected_profile()

    def _selected_profile(self) -> dict | None:
        item = self.profile_list.currentItem()
        if item is None:
            return None
        profile_id = item.data(Qt.UserRole)
        return next(
            (
                profile
                for profile in self._profiles
                if profile["id"] == profile_id
            ),
            None,
        )

    def _load_selected_profile(self, *_args) -> None:
        profile = self._selected_profile()
        enabled = profile is not None
        self.editor_card.setEnabled(enabled)
        self.duplicate_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.error_label.hide()

        self._loading_profile = True
        try:
            self.name_input.setText(profile["name"] if profile else "")
            self.endpoint_input.setText(profile["endpoint"] if profile else "")
            self.model_input.setText(profile["model"] if profile else "")
            self.api_key_input.setText(profile["api_key"] if profile else "")
        finally:
            self._loading_profile = False

    def _stage_current_profile(self, *_args) -> None:
        if self._loading_profile:
            return
        profile = self._selected_profile()
        if profile is None:
            return

        profile.update(
            {
                "name": self.name_input.text(),
                "endpoint": self.endpoint_input.text(),
                "model": self.model_input.text(),
                "api_key": self.api_key_input.text(),
            }
        )
        item = self.profile_list.currentItem()
        item.setText(profile["name"].strip() or "Untitled profile")
        item.setToolTip(profile["endpoint"].strip())
        self.error_label.hide()

    def _add_profile(self) -> None:
        profile = {
            "id": new_profile_id(),
            "name": self._available_name("New profile"),
            "endpoint": "",
            "model": "",
            "api_key": "",
        }
        self._profiles.append(profile)
        self._refresh_list(profile["id"])
        self.name_input.setFocus()
        self.name_input.selectAll()

    def _duplicate_selected(self) -> None:
        selected = self._selected_profile()
        if selected is None:
            return
        duplicate = deepcopy(selected)
        duplicate["id"] = new_profile_id()
        duplicate["name"] = self._available_name(f'{selected["name"]} copy')
        self._profiles.append(duplicate)
        self._refresh_list(duplicate["id"])
        self.name_input.setFocus()
        self.name_input.selectAll()

    def _available_name(self, preferred_name: str) -> str:
        existing_names = {
            profile["name"].strip().casefold() for profile in self._profiles
        }
        candidate = preferred_name
        suffix = 2
        while candidate.casefold() in existing_names:
            candidate = f"{preferred_name} {suffix}"
            suffix += 1
        return candidate

    def _delete_selected(self) -> None:
        selected = self._selected_profile()
        if selected is None:
            return

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Delete LLM profile")
        message_box.setText(f'Delete "{selected["name"]}"?')
        message_box.setInformativeText(
            "The endpoint, model, and saved API key will be removed when "
            "Settings are saved."
        )
        message_box.setIcon(QMessageBox.Warning)
        delete_button = message_box.addButton(
            "Delete profile", QMessageBox.DestructiveRole
        )
        cancel_button = message_box.addButton("Cancel", QMessageBox.RejectRole)
        message_box.setDefaultButton(cancel_button)
        delete_button.setIcon(QIcon())
        cancel_button.setIcon(QIcon())
        delete_button.setProperty("role", "danger")
        cancel_button.setProperty("role", "secondary")
        message_box.exec()
        if message_box.clickedButton() is not delete_button:
            return

        self._profiles.remove(selected)
        self._refresh_list()

    def _validate_and_accept(self) -> None:
        self._stage_current_profile()
        validated_profiles = []
        for profile in self._profiles:
            try:
                validated = validate_profile(
                    profile,
                    self._profiles,
                    editing_profile_id=profile["id"],
                )
            except LLMProfileValidationError as error:
                self._select_profile(profile["id"])
                self.error_label.setText(str(error))
                self.error_label.show()
                return
            validated_profiles.append(validated)

        self._profiles = validated_profiles
        self.accept()

    def _select_profile(self, profile_id: str) -> None:
        for row in range(self.profile_list.count()):
            item = self.profile_list.item(row)
            if item.data(Qt.UserRole) == profile_id:
                self.profile_list.setCurrentItem(item)
                return

    def profiles(self) -> list[dict]:
        return deepcopy(self._profiles)
