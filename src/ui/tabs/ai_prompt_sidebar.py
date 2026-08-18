from pathlib import Path

from PySide6.QtCore import QMimeData, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.components.placeholder import Placeholder
from ui.dialogs.prompt_editor import PromptEditorDialog
from storage.prompts_store import PromptsStore
from ui.resources import ADD_ICON_DARK, COPY_ICON_DARK, PASTE_ICON_DARK, SYNC_ICON_DARK


class ElidedLabel(QLabel):
    """Displays one elided line while retaining the complete source text."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full_text = text
        self.setTextFormat(Qt.PlainText)
        self.setText(text)

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self._update_elision()

    def resizeEvent(self, event):
        self._update_elision()
        super().resizeEvent(event)

    def _update_elision(self) -> None:
        available_width = max(0, self.contentsRect().width())
        self.setText(
            self.fontMetrics().elidedText(
                self._full_text,
                Qt.ElideRight,
                available_width,
            )
        )


class ClickableContextRow(QFrame):
    """Keyboard-accessible row used to expand or collapse contextual content."""

    activated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._clickable = False
        self._summary_label = None
        self.setObjectName("context_summary_row")
        self.setFocusPolicy(Qt.NoFocus)

    def set_summary_label(self, label: QLabel) -> None:
        self._summary_label = label


    def is_clickable(self) -> bool:
        return self._clickable

    def set_clickable(self, clickable: bool, description: str = "") -> None:
        self._clickable = clickable
        self.setCursor(Qt.PointingHandCursor if clickable else Qt.ArrowCursor)
        self.setFocusPolicy(Qt.StrongFocus if clickable else Qt.NoFocus)
        self.setAccessibleDescription(description if clickable else "")
        if not clickable:
            self._set_hovered(False)

    def click(self) -> None:
        if self._clickable:
            self.activated.emit()

    def mouseReleaseEvent(self, event):
        if self._clickable and event.button() == Qt.LeftButton:
            self.activated.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self._clickable and event.key() in (
            Qt.Key_Return,
            Qt.Key_Enter,
            Qt.Key_Space,
        ):
            self.activated.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def enterEvent(self, event):
        self._set_hovered(self._clickable)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_hovered(False)
        super().leaveEvent(event)

    def _set_hovered(self, hovered: bool) -> None:
        if self._summary_label is None:
            return
        font = self._summary_label.font()
        font.setUnderline(hovered)
        self._summary_label.setFont(font)
        self._summary_label.setProperty("contextHovered", hovered)
        self._summary_label.style().unpolish(self._summary_label)
        self._summary_label.style().polish(self._summary_label)


class PromptListRow(QWidget):
    editRequested = Signal(str)
    activationRequested = Signal(str)
    deleteRequested = Signal(str)

    def __init__(self, prompt_name: str, parent=None):
        super().__init__(parent)
        self.prompt_name = prompt_name
        self.setObjectName("prompt_list_row")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 0, 2, 0)
        layout.setSpacing(2)

        label = QLabel(prompt_name)
        label.setObjectName("prompt_list_name")
        label.setToolTip(prompt_name)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(label, 1)

        self.actions_button = QToolButton()
        self.actions_button.setObjectName("prompt_actions_button")
        self.actions_button.setText("...")
        self.actions_button.setCursor(Qt.PointingHandCursor)
        self.actions_button.setFocusPolicy(Qt.NoFocus)
        self.actions_button.clicked.connect(self._show_actions_menu)
        self.actions_button.hide()
        layout.addWidget(self.actions_button)

    def enterEvent(self, event):
        self.actions_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.actions_button.hide()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.activationRequested.emit(self.prompt_name)
            event.accept()
            return
        super().mouseReleaseEvent(event)


    def _show_actions_menu(self):
        menu = QMenu(self)
        menu.setObjectName("prompt_actions_menu")
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        selected_action = menu.exec(
            self.actions_button.mapToGlobal(QPoint(0, self.actions_button.height()))
        )
        if selected_action == edit_action:
            self.editRequested.emit(self.prompt_name)
        elif selected_action == delete_action:
            self.deleteRequested.emit(self.prompt_name)


class AIPromptSidebarTab(QWidget):
    promptExecutionRequested = Signal()
    BASE_MAX_INPUT_PREVIEW_HEIGHT = 220
    MAX_INPUT_PREVIEW_RATIO = 0.35

    def __init__(
        self,
        prompt_store: PromptsStore | None = None,
        clipboard_service=None,
    ):
        super().__init__()
        self.prompt_store = prompt_store
        self.clipboard_service = clipboard_service
        self.prompt_config = {}
        self._ai_enabled = True
        self._has_prompt = False
        self._prompt_expanded = False
        self._has_input = False
        self._input_expanded = False
        self.setObjectName("ai_prompt_tab")
        self._setup_ui()
        self.reload_prompts(show_feedback=False)

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sidebar.setFixedWidth(123)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.prompts_header = QFrame()
        self.prompts_header.setObjectName("prompts_header")
        title_row = QHBoxLayout(self.prompts_header)
        title_row.setContentsMargins(8, 0, 2, 0)
        title_row.setSpacing(0)
        self.prompts_title = QLabel("Prompts")
        self.prompts_title.setObjectName("section_label")
        title_row.addWidget(self.prompts_title)
        title_row.addStretch(1)

        self.open_prompts_store_button = QToolButton()
        self.open_prompts_store_button.setObjectName("open_prompts_store_button")
        self.open_prompts_store_button.setText("+")
        self.open_prompts_store_button.setIcon(ADD_ICON_DARK)
        self.open_prompts_store_button.setToolTip("Add prompt")
        self.open_prompts_store_button.setCursor(Qt.PointingHandCursor)
        self.open_prompts_store_button.clicked.connect(self._open_prompt_editor)

        self.reload_prompts_button = QToolButton()
        self.reload_prompts_button.setObjectName("reload_prompts_button")
        self.reload_prompts_button.setIcon(SYNC_ICON_DARK)
        self.reload_prompts_button.setToolTip("Reload prompts")
        self.reload_prompts_button.setCursor(Qt.PointingHandCursor)
        self.reload_prompts_button.clicked.connect(self.reload_prompts)

        header_actions = QHBoxLayout()
        header_actions.setContentsMargins(0, 0, 0, 0)
        header_actions.setSpacing(2)
        header_actions.addWidget(self.open_prompts_store_button)
        header_actions.addWidget(self.reload_prompts_button)
        title_row.addLayout(header_actions)

        sidebar_layout.addWidget(self.prompts_header)

        self.prompts_list = QListWidget()
        self.prompts_list.setObjectName("prompts_list")
        self.prompts_list.itemClicked.connect(self._on_prompt_clicked)
        sidebar_layout.addWidget(self.prompts_list, 1)

        root.addWidget(sidebar)

        content = QFrame()
        content.setObjectName("card")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 10, 14, 10)
        content_layout.setSpacing(5)

        self.prompt_context_card = QFrame()
        self.prompt_context_card.setObjectName("prompt_context_card")
        prompt_context_layout = QVBoxLayout(self.prompt_context_card)
        prompt_context_layout.setContentsMargins(0, 0, 0, 0)
        prompt_context_layout.setSpacing(4)

        self.prompt_header = ClickableContextRow()
        prompt_header_layout = QHBoxLayout(self.prompt_header)
        prompt_header_layout.setContentsMargins(0, 0, 0, 0)
        prompt_header_layout.setSpacing(8)
        self.prompt_label = QLabel("Prompt")
        self.prompt_label.setObjectName("section_label")
        prompt_header_layout.addWidget(self.prompt_label)

        self.prompt_summary = ElidedLabel("No prompt selected")
        self.prompt_summary.setObjectName("prompt_summary")
        prompt_header_layout.addWidget(self.prompt_summary, 1)
        self.prompt_header.set_summary_label(self.prompt_summary)
        self.prompt_header.activated.connect(self._toggle_prompt_preview)
        prompt_context_layout.addWidget(self.prompt_header)

        self.ai_input_prompt = QLabel()
        self.ai_input_prompt.setObjectName("ai_input_prompt")
        self.ai_input_prompt.setTextFormat(Qt.PlainText)
        self.ai_input_prompt.setWordWrap(True)
        self.ai_input_prompt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ai_input_prompt.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )
        self.ai_input_prompt.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ai_input_prompt.hide()
        prompt_context_layout.addWidget(self.ai_input_prompt)
        content_layout.addWidget(self.prompt_context_card)

        self.input_context_card = QFrame()
        self.input_context_card.setObjectName("input_context_card")
        input_context_layout = QVBoxLayout(self.input_context_card)
        input_context_layout.setContentsMargins(0, 0, 0, 0)
        input_context_layout.setSpacing(4)

        self.input_header = ClickableContextRow()
        input_header_layout = QHBoxLayout(self.input_header)
        input_header_layout.setContentsMargins(0, 0, 0, 0)
        input_header_layout.setSpacing(8)
        self.input_label = QLabel("Input")
        self.input_label.setObjectName("section_label")
        input_header_layout.addWidget(self.input_label)

        self.input_summary = ElidedLabel("No copied input")
        self.input_summary.setObjectName("input_summary")
        input_header_layout.addWidget(self.input_summary, 1)
        self.input_header.set_summary_label(self.input_summary)
        self.input_header.activated.connect(self._toggle_input_preview)
        input_context_layout.addWidget(self.input_header)

        self.input_data_placeholder = Placeholder(self)
        self.input_data_placeholder.setObjectName("input_data_placeholder")
        self.input_data_placeholder.setAttribute(Qt.WA_StyledBackground, True)
        self.input_scroll = QScrollArea()
        self.input_scroll.setObjectName("ai_input_scroll")
        self.input_scroll.setWidgetResizable(True)
        self.input_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.input_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_scroll.setWidget(self.input_data_placeholder)
        self.input_scroll.hide()
        input_context_layout.addWidget(self.input_scroll)
        content_layout.addWidget(self.input_context_card)

        output_header = QHBoxLayout()
        output_header.setSpacing(8)
        output_header.setContentsMargins(0, 0, 0, 1)
        self.output_label = QLabel("Output")
        self.output_label.setObjectName("section_label")
        output_header.addWidget(self.output_label)
        self.request_status = ElidedLabel()
        self.request_status.setObjectName("ai_request_status")
        self.request_status.setTextFormat(Qt.PlainText)
        self.request_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.request_status.hide()
        output_header.addWidget(self.request_status, 1)

        self.request_state = QLabel()
        self.request_state.setObjectName("ai_request_state")
        self.request_state.hide()
        output_header.addWidget(self.request_state)
        content_layout.addLayout(output_header)

        self.ai_output_text = QLabel("Click a prompt to run it.")
        self.ai_output_text.setObjectName("ai_output_text")
        self.ai_output_text.setTextFormat(Qt.MarkdownText)
        self.ai_output_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ai_output_text.setWordWrap(True)
        self.ai_output_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        )
        self.output_card = QFrame()
        self.output_card.setObjectName("output_card")
        self.output_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        output_card_layout = QGridLayout(self.output_card)
        output_card_layout.setContentsMargins(0, 0, 0, 0)
        output_card_layout.setSpacing(0)

        self.output_scroll = QScrollArea()
        self.output_scroll.setObjectName("ai_output_scroll")
        self.output_scroll.setWidgetResizable(True)
        self.output_scroll.setFrameShape(QFrame.NoFrame)
        self.output_scroll.setWidget(self.ai_output_text)
        output_card_layout.addWidget(self.output_scroll, 0, 0)
        output_card_layout.setRowStretch(0, 1)

        self.output_actions_container = QFrame()
        self.output_actions_container.setObjectName("output_actions_container")
        output_actions = QHBoxLayout(self.output_actions_container)
        output_actions.setContentsMargins(0, 4, 0, 0)
        output_actions.setSpacing(2)
        output_actions.setAlignment(Qt.AlignLeft)

        self.copy_output_button = QToolButton()
        self.copy_output_button.setObjectName("output_action_button")
        self.copy_output_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.copy_output_button.setIcon(COPY_ICON_DARK)
        self.copy_output_button.setToolTip("Copy output")
        self.copy_output_button.setCursor(Qt.PointingHandCursor)
        self.copy_output_button.clicked.connect(
            lambda: self._handle_copy_output_click(self.ai_output_text.text())
        )
        output_actions.addWidget(self.copy_output_button)

        self.paste_output_button = QToolButton()
        self.paste_output_button.setObjectName("output_action_button")
        self.paste_output_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.paste_output_button.setIcon(PASTE_ICON_DARK)
        self.paste_output_button.setToolTip("Paste output")
        self.paste_output_button.setCursor(Qt.PointingHandCursor)
        self.paste_output_button.clicked.connect(
            lambda: self._handle_paste_output_click(self.ai_output_text.text())
        )
        output_actions.addWidget(self.paste_output_button)
        output_actions.addStretch(1)

        output_card_layout.addWidget(self.output_actions_container, 1, 0)
        content_layout.addWidget(self.output_card, 1)

        root.addWidget(content)
        self.setLayout(root)

    def _setup_styles(self):
        self.setStyleSheet(
            """
        QWidget { background: #f5f7fb; color: #1f2933; }
        QFrame#sidebar, QFrame#card {
            background: #ffffff;
            border: 1px solid #ffffff;
            margin: 0px;
            border-radius: 0px;
        }
        QLabel#section_label {
            border: none;
            background: transparent;
            padding: 0;
            font-size: 14px;
            text-transform: none;
            font-weight: 700;
            color: #52606d;
        }
        QLabel#ai_input_prompt, QLabel#ai_output_text {
            color: #263238;
            margin: 0;
            border: 1px solid rgba(30,36,44,0.06);
            padding: 8px 10px;
            background: #fbfdff;
            border-radius: 8px;
        }
        QFrame#output_card {
            background: transparent;
            border: none;
        }
        QFrame#output_actions_container {
            background: rgba(255, 255, 255, 0.94);
            border: 0px solid rgba(30,36,44,0.08);
            border-radius: 8px;
            padding: 0px;
            margin: 1px;
        }
        QListWidget#prompts_list {
            border: 1px solid rgba(30,36,44,0.06);
            border-radius: 8px;
            background: #fbfdff;
            padding: 4px;
            outline: none;
        }
        QListWidget#prompts_list::item {
            padding: 4px 6px;
            border-radius: 6px;
            margin: 0px 0;
        }
        QListWidget#prompts_list::item:selected {
            background: #d9e8ff;
            color: #163a70;
        }
        QListWidget#prompts_list::item:hover {
            background: #eef4ff;
            border-radius: 6px;
        }
        QToolButton#open_prompts_store_button,
        QToolButton#reload_prompts_button {
            background: transparent;
            border: none;
            min-width: 22px;
            min-height: 22px;
            padding: 0px;
            color: #52606d;
            font-size: 14px;
            font-weight: 700;
        }
        QToolButton#open_prompts_store_button:hover,
        QToolButton#reload_prompts_button:hover {
            background: #eef4ff;
            border-radius: 6px;
        }
        QToolButton#output_action_button {
            background: transparent;
            border: none;
            min-width: 24px;
            min-height: 24px;
            padding: 0px;
            margin: 0px;
        }
        QToolButton#output_action_button:hover {
            background: #eef4ff;
            border-radius: 6px;
        }
        QLabel#ai_output_text {
            background: #ffffff;
            padding-top: 18px;
            padding-right: 64px;
        }
        """
        )
        self.input_data_placeholder.setStyleSheet(
            """
            font-weight: 500;
            color: #263238;
            margin: 0;
            border: 1px solid rgba(30,36,44,0.06);
            padding: 8px 10px;
            background: #fbfdff;
            border-radius: 8px;
        """
        )

    def _ensure_prompt_file_exists(self):
        if not self.prompt_store:
            return

        store_path = Path(self.prompt_store.store_path)
        store_path.parent.mkdir(parents=True, exist_ok=True)
        if store_path.exists():
            return

        store_path.write_text(
            '[summarize]\nprompt = "Summarize this clipboard item."\n',
            encoding="utf-8",
        )

    def _open_prompt_editor(self):
        self._edit_prompt()

    def _edit_prompt(self, prompt_name: str | None = None):
        if not self.prompt_store:
            return
        if prompt_name is not None and prompt_name not in self.prompt_config:
            return

        self._ensure_prompt_file_exists()
        dialog = PromptEditorDialog(
            self.prompt_config,
            self,
            editing_prompt_name=prompt_name,
        )
        if dialog.exec():
            try:
                self.prompt_store.save_prompts(dialog.get_prompt_config())
                self.reload_prompts(show_feedback=False)
                saved_name = dialog.get_saved_prompt_name()
                self._select_prompt_item(saved_name)
            except Exception as exc:
                self.show_error("Prompt Error", str(exc))

    def _delete_prompt(self, prompt_name: str):
        if not self.prompt_store or prompt_name not in self.prompt_config:
            return

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Delete prompt")
        message_box.setText(f"Delete '{prompt_name}'?")
        message_box.setInformativeText("This action cannot be undone.")
        message_box.setIcon(QMessageBox.Warning)

        delete_button = message_box.addButton(
            "Delete prompt",
            QMessageBox.DestructiveRole,
        )
        cancel_button = message_box.addButton("Cancel", QMessageBox.RejectRole)
        message_box.setDefaultButton(cancel_button)
        delete_button.setIcon(QIcon())
        cancel_button.setIcon(QIcon())

        delete_button.setProperty("role", "danger")
        cancel_button.setProperty("role", "secondary")
        for button in (delete_button, cancel_button):
            button.style().unpolish(button)
            button.style().polish(button)

        message_box.exec()
        if message_box.clickedButton() is not delete_button:
            return

        current_item = self.prompts_list.currentItem()
        selected_name = (
            current_item.data(Qt.UserRole) if current_item is not None else None
        )
        updated_config = dict(self.prompt_config)
        del updated_config[prompt_name]
        try:
            self.prompt_store.save_prompts(updated_config)
            self.reload_prompts(show_feedback=False)
            if selected_name == prompt_name:
                self.clear_prompt()
            else:
                self._select_prompt_item(selected_name)
        except Exception as exc:
            self.show_error("Prompt Error", str(exc))

    def _normalize_prompt_name(self, prompt_name: str) -> str:
        return " ".join(prompt_name.split()).casefold()

    def _validated_prompt_map(self) -> dict:
        if not self.prompt_store:
            return {}

        prompt_config = self.prompt_store.prompt_config or {}
        normalized_names = {}
        validated = {}

        for key, value in prompt_config.items():
            if not isinstance(value, dict):
                continue

            prompt_name = str(value.get("name", key)).strip()
            normalized_name = self._normalize_prompt_name(prompt_name)
            if normalized_name in normalized_names:
                raise ValueError(
                    f"Duplicate prompt names found: '{normalized_names[normalized_name]}' and '{prompt_name}'."
                )

            normalized_names[normalized_name] = prompt_name
            validated[prompt_name] = value

        return validated

    def _populate_prompt_list(self):
        self.prompts_list.clear()
        for prompt_name in self.prompt_config.keys():
            item = QListWidgetItem()
            item.setData(Qt.UserRole, prompt_name)
            item.setSizeHint(QSize(0, 30))
            row = PromptListRow(prompt_name, self.prompts_list)
            row.activationRequested.connect(self._on_prompt_row_activated)
            row.editRequested.connect(self._edit_prompt)
            row.deleteRequested.connect(self._delete_prompt)
            self.prompts_list.addItem(item)
            self.prompts_list.setItemWidget(item, row)

    def _select_prompt_item(self, prompt_name: str | None):
        if not prompt_name:
            return
        for row in range(self.prompts_list.count()):
            item = self.prompts_list.item(row)
            if item.data(Qt.UserRole) == prompt_name:
                self.prompts_list.setCurrentItem(item)
                return

    def reload_prompts(self, show_feedback: bool = True):
        if not self.prompt_store:
            self.prompt_config = {}
            self.prompts_list.clear()
            return

        self.prompt_store.load_prompts()

        try:
            if self.prompt_store.last_error:
                raise ValueError(self.prompt_store.last_error)

            self.prompt_config = self._validated_prompt_map()
            self._populate_prompt_list()
        except Exception as exc:
            self.prompt_config = {}
            self.prompts_list.clear()
            self.clear_prompt()
            self.show_error("Prompt Error", str(exc))
            return

    def _on_prompt_clicked(self, item: QListWidgetItem):
        prompt_name = item.data(Qt.UserRole)
        self._execute_prompt(prompt_name)

    def _on_prompt_row_activated(self, prompt_name: str):
        self._select_prompt_item(prompt_name)
        self._execute_prompt(prompt_name)

    def _execute_prompt(self, prompt_name: str):
        prompt_text = self.prompt_config.get(prompt_name, {}).get("prompt", "")
        self.set_prompt(prompt_text, prompt_name)
        self.promptExecutionRequested.emit()

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def is_ai_enabled(self):
        return self._ai_enabled

    def set_ai_enabled(self, enabled: bool):
        self._ai_enabled = enabled

    def get_selected_prompt(self):
        current_item = self.prompts_list.currentItem()
        if current_item is None:
            return ""

        prompt_name = current_item.data(Qt.UserRole)
        return self.prompt_config.get(prompt_name, {}).get("prompt", "")

    def set_prompt(self, prompt, prompt_name: str | None = None):
        prompt = str(prompt or "")
        self._has_prompt = bool(prompt)
        self._set_content_label_state(self.prompt_label, self._has_prompt)
        self.ai_input_prompt.setText(prompt)
        if self._has_prompt:
            prompt_name = prompt_name or self.get_selected_prompt_name()
            one_line_prompt = " ".join(prompt.split())
            summary = (
                f"{prompt_name} · {one_line_prompt}"
                if prompt_name
                else one_line_prompt
            )
            self.prompt_summary.set_full_text(summary)
        else:
            self.prompt_summary.set_full_text("No prompt selected")
        self._apply_prompt_preview_state()

    def clear_prompt(self):
        self.set_prompt("")

    def get_selected_prompt_name(self):
        current_item = self.prompts_list.currentItem()
        return current_item.data(Qt.UserRole) if current_item else ""

    def _toggle_prompt_preview(self):
        if not self._has_prompt:
            return
        self._prompt_expanded = not self._prompt_expanded
        self._apply_prompt_preview_state()

    def _apply_prompt_preview_state(self):
        expanded = self._has_prompt and self._prompt_expanded
        self.ai_input_prompt.setVisible(expanded)
        action = "Hide prompt" if expanded else "Show prompt"
        self.prompt_header.set_clickable(self._has_prompt, action)

    def set_input_data(self, input_data_widget, summary: str = ""):
        self._has_input = input_data_widget is not None
        self._set_content_label_state(self.input_label, self._has_input)
        if self._has_input:
            self.input_data_placeholder.set_widget(input_data_widget)
            self.input_summary.set_full_text(summary or "Copied input")
        else:
            self.input_data_placeholder.clear()
            self.input_summary.set_full_text("No copied input")

        self._apply_input_preview_state()

    @staticmethod
    def _set_content_label_state(label: QLabel, has_content: bool):
        label.setProperty("hasContent", has_content)
        label.style().unpolish(label)
        label.style().polish(label)

    def clear_input_data(self):
        self.set_input_data(None)

    def _toggle_input_preview(self):
        if not self._has_input:
            return
        self._input_expanded = not self._input_expanded
        self._apply_input_preview_state()

    def _apply_input_preview_state(self):
        expanded = self._has_input and self._input_expanded
        self.input_scroll.setVisible(expanded)
        action = "Hide input" if expanded else "Show input"
        self.input_header.set_clickable(self._has_input, action)
        if expanded:
            QTimer.singleShot(0, self._update_input_placeholder_height)

    def set_request_status(
        self,
        status: str = "",
        request_active: bool = True,
    ):
        state = ""
        for candidate in ("Complete", "Failed"):
            suffix = f" · {candidate}"
            if status.endswith(suffix):
                status = status[: -len(suffix)]
                state = candidate
                break

        self.request_status.set_full_text(status)
        self.request_status.setVisible(bool(status))
        self.request_state.setText(f"· {state}" if state else "")
        state_name = state.casefold() if state else (
            "running" if status and request_active else ""
        )
        self.request_state.setProperty("state", state.casefold())
        self.request_state.setVisible(bool(state))
        self.request_state.style().unpolish(self.request_state)
        self.request_state.style().polish(self.request_state)
        self.output_label.setProperty("llmState", state_name)
        self.output_label.style().unpolish(self.output_label)
        self.output_label.style().polish(self.output_label)

    def _handle_copy_output_click(self, text: str):
        self._set_output_clipboard(text, trigger_paste=False)

    def _handle_paste_output_click(self, text: str):
        self._set_output_clipboard(text, trigger_paste=True)

    def _set_output_clipboard(self, text: str, trigger_paste: bool):
        if not self.clipboard_service or not text:
            return

        mime_data = QMimeData()
        mime_data.setText(text)
        self.clipboard_service.set_clipboard(
            mime_data,
            trigger_paste=trigger_paste,
        )

    def resizeEvent(self, event):
        if self._input_expanded:
            self._update_input_placeholder_height()
        super().resizeEvent(event)

    def _input_preview_height_cap(self):
        return max(
            120,
            min(
                self.BASE_MAX_INPUT_PREVIEW_HEIGHT,
                int(self.height() * self.MAX_INPUT_PREVIEW_RATIO),
            ),
        )

    def _update_input_placeholder_height(self):
        if not self._has_input or not self._input_expanded:
            return

        content_height = self.input_data_placeholder.sizeHint().height()
        frame_height = self.input_scroll.frameWidth() * 2
        scrollbar_height = self.input_scroll.horizontalScrollBar().sizeHint().height()
        height_cap = self._input_preview_height_cap()
        target_height = max(56, min(content_height + frame_height, height_cap))

        needs_horizontal_scroll = (
            self.input_data_placeholder.sizeHint().width() > self.input_scroll.viewport().width()
        )
        if needs_horizontal_scroll:
            target_height = min(
                target_height + scrollbar_height,
                height_cap,
            )

        self.input_scroll.setFixedHeight(target_height)

    def set_ai_output(self, ai_output_text):
        self.ai_output_text.setText(ai_output_text)
