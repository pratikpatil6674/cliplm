from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QPoint, QSize, Qt, QTimer, Signal
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
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from PlaceHolder import Placeholder
from PromptEditorDialog import PromptEditorDialog
from PromptsStore import PromptsStore
from resources import ADD_ICON_DARK, COPY_ICON_DARK, PASTE_ICON_DARK, SYNC_ICON_DARK


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
        self._output_actions_visible = False
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
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 12, 10, 12)
        sidebar_layout.setSpacing(6)

        title_row = QHBoxLayout()
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
        title_row.addWidget(self.open_prompts_store_button)

        self.reload_prompts_button = QToolButton()
        self.reload_prompts_button.setObjectName("reload_prompts_button")
        self.reload_prompts_button.setIcon(SYNC_ICON_DARK)
        self.reload_prompts_button.setToolTip("Reload prompts")
        self.reload_prompts_button.setCursor(Qt.PointingHandCursor)
        self.reload_prompts_button.clicked.connect(self.reload_prompts)
        title_row.addWidget(self.reload_prompts_button)

        sidebar_layout.addLayout(title_row)

        self.prompts_list = QListWidget()
        self.prompts_list.setObjectName("prompts_list")
        self.prompts_list.itemClicked.connect(self._on_prompt_clicked)
        sidebar_layout.addWidget(self.prompts_list, 1)

        root.addWidget(sidebar)

        content = QFrame()
        content.setObjectName("card")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(7)

        self.prompt_label = QLabel("Prompt")
        self.prompt_label.setObjectName("section_label")
        content_layout.addWidget(self.prompt_label)

        self.ai_input_prompt = QLabel()
        self.ai_input_prompt.setObjectName("ai_input_prompt")
        self.ai_input_prompt.setTextFormat(Qt.PlainText)
        self.ai_input_prompt.setWordWrap(True)
        prompt_size_policy = QSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        prompt_size_policy.setHeightForWidth(True)
        self.ai_input_prompt.setSizePolicy(prompt_size_policy)
        self.ai_input_prompt.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(self.ai_input_prompt)

        self.input_label = QLabel("Input")
        self.input_label.setObjectName("section_label")
        content_layout.addWidget(self.input_label)

        self.input_data_placeholder = Placeholder(self)
        self.input_data_placeholder.setObjectName("input_data_placeholder")
        self.input_scroll = QScrollArea()
        self.input_scroll.setWidgetResizable(True)
        self.input_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.input_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.input_scroll.setWidget(self.input_data_placeholder)
        content_layout.addWidget(self.input_scroll)

        self.output_label = QLabel("Output")
        self.output_label.setObjectName("section_label")
        content_layout.addWidget(self.output_label)

        self.ai_output_text = QLabel("AI Output")
        self.ai_output_text.setObjectName("ai_output_text")
        self.ai_output_text.setTextFormat(Qt.MarkdownText)
        self.ai_output_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.ai_output_text.setWordWrap(True)
        self.ai_output_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
        )
        self.output_card = QFrame()
        self.output_card.setObjectName("output_card")
        self.output_card.installEventFilter(self)
        output_card_layout = QGridLayout(self.output_card)
        output_card_layout.setContentsMargins(0, 0, 0, 0)
        output_card_layout.setSpacing(0)

        self.output_scroll = QScrollArea()
        self.output_scroll.setWidgetResizable(True)
        self.output_scroll.setFrameShape(QFrame.NoFrame)
        self.output_scroll.setWidget(self.ai_output_text)
        self.output_scroll.viewport().installEventFilter(self)
        output_card_layout.addWidget(self.output_scroll, 0, 0)

        self.output_actions_container = QFrame(self.output_card)
        self.output_actions_container.setObjectName("output_actions_container")
        self.output_actions_container.installEventFilter(self)
        output_actions = QHBoxLayout(self.output_actions_container)
        output_actions.setContentsMargins(0, 0, 0, 0)
        output_actions.setSpacing(0)

        self.copy_output_button = QToolButton()
        self.copy_output_button.setObjectName("output_action_button")
        self.copy_output_button.setIcon(COPY_ICON_DARK)
        self.copy_output_button.setToolTip("Copy output")
        self.copy_output_button.setCursor(Qt.PointingHandCursor)
        self.copy_output_button.clicked.connect(
            lambda: self._handle_copy_output_click(self.ai_output_text.text())
        )
        output_actions.addWidget(self.copy_output_button)

        self.paste_output_button = QToolButton()
        self.paste_output_button.setObjectName("output_action_button")
        self.paste_output_button.setIcon(PASTE_ICON_DARK)
        self.paste_output_button.setToolTip("Paste output")
        self.paste_output_button.setCursor(Qt.PointingHandCursor)
        self.paste_output_button.clicked.connect(
            lambda: self._handle_paste_output_click(self.ai_output_text.text())
        )
        output_actions.addWidget(self.paste_output_button)

        output_card_layout.addWidget(
            self.output_actions_container,
            0,
            0,
            alignment=Qt.AlignTop | Qt.AlignRight,
        )
        self.output_actions_container.hide()
        content_layout.addWidget(self.output_card)

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
                action = "Updated" if prompt_name else "Added"
                self.ai_output_text.setText(f"{action} '{saved_name}'.")
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
                self.ai_input_prompt.clear()
            else:
                self._select_prompt_item(selected_name)
            self.ai_output_text.setText(f"Deleted '{prompt_name}'.")
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

        if self.prompts_list.count() > 0:
            self.prompts_list.setCurrentRow(0)

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
            self.ai_input_prompt.clear()
            self.ai_output_text.setText("Prompt reload failed.")
            self.show_error("Prompt Error", str(exc))
            return

        if show_feedback:
            self.ai_output_text.setText(f"Loaded {len(self.prompt_config)} prompt(s).")

    def _on_prompt_clicked(self, item: QListWidgetItem):
        prompt_name = item.data(Qt.UserRole)
        self._execute_prompt(prompt_name)

    def _on_prompt_row_activated(self, prompt_name: str):
        self._select_prompt_item(prompt_name)
        self._execute_prompt(prompt_name)

    def _execute_prompt(self, prompt_name: str):
        prompt_text = self.prompt_config.get(prompt_name, {}).get("prompt", "")
        self.set_prompt(prompt_text)
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

    def set_prompt(self, prompt):
        self.ai_input_prompt.setText(prompt)
        self.ai_input_prompt.updateGeometry()
        QTimer.singleShot(0, self._update_prompt_height)

    def set_input_data(self, input_data_widget):
        self.input_data_placeholder.set_widget(input_data_widget)
        self._update_input_placeholder_height()

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

    def eventFilter(self, watched, event):
        if not all(
            hasattr(self, attr)
            for attr in (
                "output_card",
                "output_scroll",
                "output_actions_container",
                "copy_output_button",
                "paste_output_button",
            )
        ):
            return super().eventFilter(watched, event)

        if watched in {
            self.output_card,
            self.output_scroll.viewport(),
            self.output_actions_container,
        }:
            if event.type() == QEvent.Enter:
                self._set_output_actions_visible(True)
            elif event.type() == QEvent.Leave:
                QTimer.singleShot(0, self._refresh_output_actions_visibility)
        return super().eventFilter(watched, event)

    def _refresh_output_actions_visibility(self):
        should_show = (
            self.output_card.underMouse()
            or self.output_scroll.viewport().underMouse()
            or self.output_actions_container.underMouse()
            or self.copy_output_button.underMouse()
            or self.paste_output_button.underMouse()
        )
        self._set_output_actions_visible(should_show)

    def _set_output_actions_visible(self, visible: bool):
        if self._output_actions_visible == visible:
            return

        self._output_actions_visible = visible
        self.output_actions_container.setVisible(visible)

    def resizeEvent(self, event):
        # Recompute the preview height when the tab is resized so the cap grows
        # with the available space instead of staying stuck at a fixed value.
        self._update_input_placeholder_height()
        QTimer.singleShot(0, self._update_prompt_height)
        super().resizeEvent(event)

    def _update_prompt_height(self):
        prompt_width = self.ai_input_prompt.width()
        if prompt_width <= 0:
            return

        required_height = self.ai_input_prompt.heightForWidth(prompt_width)
        if required_height > 0 and self.ai_input_prompt.height() != required_height:
            self.ai_input_prompt.setFixedHeight(required_height)

    def _input_preview_height_cap(self):
        # Let the cap scale with the current tab height, while keeping a sane
        # minimum for smaller windows.
        return max(
            self.BASE_MAX_INPUT_PREVIEW_HEIGHT,
            int(self.height() * self.MAX_INPUT_PREVIEW_RATIO),
        )

    def _update_input_placeholder_height(self):
        # Use the content height when it is small, but clamp it to a dynamic cap
        # so larger windows can show more preview before scrolling.
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
