from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)
from ui.resources import *


class TranslateTab(QWidget):
    translateRequested = Signal()
    languageSettingsChanged = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._language_items = []
        self._syncing_scrollbars = False
        self.setObjectName("translate_tab")
        self._setup_ui()
        self._connect_scrollbars()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        controls = QFrame()
        controls.setObjectName("controls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 10, 12, 10)
        controls_layout.setSpacing(8)

        self.source_combo = QComboBox()
        self.source_combo.setObjectName("language_combo")
        self.source_combo.currentIndexChanged.connect(self._handle_language_change)
        controls_layout.addWidget(self.source_combo, 1)

        self.reverse_language_button = QToolButton()
        self.reverse_language_button.setObjectName("reverse_language_button")
        self.reverse_language_button.setCursor(Qt.PointingHandCursor)
        self.reverse_language_button.setText("⇄")
        self.reverse_language_button.setToolTip("Reverse languages")
        self.reverse_language_button.clicked.connect(self._reverse_languages)
        controls_layout.addWidget(self.reverse_language_button)

        self.destination_combo = QComboBox()
        self.destination_combo.setObjectName("language_combo")
        self.destination_combo.currentIndexChanged.connect(self._handle_language_change)
        controls_layout.addWidget(self.destination_combo, 1)

        self.translate_button = QPushButton()
        self.translate_button.setObjectName("translate_button")
        translate_button_layout = QVBoxLayout(self.translate_button)
        translate_button_layout.setContentsMargins(10, 2, 10, 2)
        translate_button_layout.setSpacing(0)

        translate_text_container = QWidget(self.translate_button)
        translate_text_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        translate_text_layout = QVBoxLayout(translate_text_container)
        translate_text_layout.setContentsMargins(0, 0, 0, 0)
        translate_text_layout.setSpacing(1)

        self.translate_action_label = QLabel("Translate")
        self.translate_action_label.setObjectName("translate_action_label")
        self.translate_action_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.translate_action_label.setAlignment(Qt.AlignCenter)
        translate_text_layout.addWidget(self.translate_action_label, 0, Qt.AlignHCenter)

        self.translate_provider_label = QLabel("with Google")
        self.translate_provider_label.setObjectName("translate_provider_label")
        self.translate_provider_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.translate_provider_label.setAlignment(Qt.AlignCenter)
        translate_text_layout.addWidget(self.translate_provider_label, 0, Qt.AlignHCenter)
        translate_button_layout.addWidget(translate_text_container, 0, Qt.AlignCenter)

        self.translate_button.setAccessibleName("Translate with Google")
        QTimer.singleShot(0, self._update_translate_button_size)
        self.translate_button.setCursor(Qt.PointingHandCursor)
        self.translate_button.clicked.connect(self.translateRequested.emit)
        controls_layout.addWidget(self.translate_button)

        layout.addWidget(controls)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        self.source_panel = QFrame()
        self.source_panel.setObjectName("translation_source_panel")
        source_panel_layout = QVBoxLayout(self.source_panel)
        source_panel_layout.setContentsMargins(1, 1, 1, 1)
        source_panel_layout.setSpacing(0)

        self.translate_src_text = QPlainTextEdit("Copy text to populate this field.")
        self.translate_src_text.setObjectName("translate_src_text")
        self.translate_src_text.viewport().setAutoFillBackground(False)
        self.translate_src_text.viewport().setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )
        source_panel_layout.addWidget(self.translate_src_text)
        card_layout.addWidget(self.source_panel)

        # QPlainTextEdit already provides scrolling; avoid nesting it in a
        # QScrollArea and use its scrollbar for synchronized translation views.
        self.source_scroll = self.translate_src_text

        self.destination_panel = QFrame()
        self.destination_panel.setObjectName("translation_destination_panel")
        destination_panel_layout = QVBoxLayout(self.destination_panel)
        destination_panel_layout.setContentsMargins(1, 1, 1, 1)
        destination_panel_layout.setSpacing(0)

        self.translated_text = QLabel("Translation output will appear here.")
        self.translated_text.setObjectName("translated_text")
        self.translated_text.setTextFormat(Qt.PlainText)
        self.translated_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translated_text.setWordWrap(True)
        self.translated_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.destination_scroll = QScrollArea()
        self.destination_scroll.setObjectName("translation_destination_scroll")
        self.destination_scroll.setWidgetResizable(True)
        self.destination_scroll.setWidget(self.translated_text)
        destination_panel_layout.addWidget(self.destination_scroll)
        card_layout.addWidget(self.destination_panel)

        layout.addWidget(card)

    def _setup_styles(self):
        self.setStyleSheet(
            """
            QWidget { background: #f5f7fb; color: #1f2933; }
            QFrame#controls, QFrame#card {
                background: #ffffff;
                border-radius: 0px;
                border: 0px solid rgba(30,36,44,0.06);
            }
            QLabel#section_label {
                border: none;
                background: transparent;
                padding: 0;
                font-size: 12px;
                font-weight: 700;
                color: #52606d;
            }
            QComboBox#language_combo {
                padding: 6px 10px;
                min-height: 30px;
                border-radius: 0px;
                border: 0px solid rgba(20,24,30,0.06);
                background: white;
                font-size: 13px;
            }
            QComboBox#language_combo:hover {
                background: #f3f8ff;
            }
            QToolButton#reverse_language_button {
                min-width: 30px;
                min-height: 30px;
                border: none;
                border-radius: 8px;
                background: transparent;
                padding: 4px;
            }
            QToolButton#reverse_language_button:hover:!disabled {
                background: #e9f2ff;
            }
            QToolButton#reverse_language_button:disabled {
                background: transparent;
            }
            QPushButton#translate_button {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                padding: 8px 10px;
                border-radius: 8px;
                text-transform: none;
                font-weight: 600;
                font-size: 12pt;
            }
            QPushButton#translate_button:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
            QFrame#translation_source_panel,
            QFrame#translation_destination_panel {
                border: 1px solid rgba(30,36,44,0.06);
                background: #fbfdff;
                border-radius: 10px;
            }
            QPlainTextEdit#translate_src_text,
            QLabel#translated_text {
                color: #263238;
                margin: 0;
                border: none;
                padding: 8px 10px;
                background: transparent;
            }
        """
        )

    def trigger_primary_action(self):
        self.translate_button.click()

    def set_translation_provider(self, provider):
        provider_labels = {
            "google": "Google",
            "llm": "LLM",
        }
        provider_label = provider_labels.get(provider, "Google")
        button_text = f"Translate with {provider_label}"
        self.translate_provider_label.setText(f"with {provider_label}")
        self.translate_button.setAccessibleName(button_text)
        self._update_translate_button_size()
        QTimer.singleShot(0, self._update_translate_button_size)

    def _update_translate_button_size(self):
        content_width = max(
            self.translate_action_label.sizeHint().width(),
            self.translate_provider_label.sizeHint().width(),
        )
        control_height = max(
            self.source_combo.sizeHint().height(),
            self.destination_combo.sizeHint().height(),
        )
        self.translate_button.setFixedSize(content_width + 20, control_height)

    def _connect_scrollbars(self):
        self.source_scroll.verticalScrollBar().valueChanged.connect(
            lambda value: self._sync_scrollbars(
                self.source_scroll.verticalScrollBar(),
                self.destination_scroll.verticalScrollBar(),
                value,
            )
        )
        self.destination_scroll.verticalScrollBar().valueChanged.connect(
            lambda value: self._sync_scrollbars(
                self.destination_scroll.verticalScrollBar(),
                self.source_scroll.verticalScrollBar(),
                value,
            )
        )

    def _sync_scrollbars(self, source_bar, target_bar, value):
        # Updating the other scrollbar emits another valueChanged signal.
        # Ignore that call so the two bars do not update each other forever.
        if self._syncing_scrollbars:
            return

        source_max = source_bar.maximum()
        target_max = target_bar.maximum()
        if target_max <= 0:
            return

        # The boxes can have different scroll ranges, so match their relative
        # positions instead of copying the raw scrollbar value.
        if source_max <= 0:
            target_value = 0
        else:
            ratio = value / source_max
            target_value = round(ratio * target_max)

        # Hold the guard only while changing the other scrollbar.
        self._syncing_scrollbars = True
        try:
            target_bar.setValue(target_value)
        finally:
            self._syncing_scrollbars = False

    def set_language_options(self, source_languages, destination_languages):
        self._language_items = list(destination_languages)
        self._populate_language_combo(self.source_combo, source_languages, "auto")
        self._populate_language_combo(self.destination_combo, destination_languages, "en")
        self._update_reverse_button_state()

        self._update_translate_button_size()
        QTimer.singleShot(0, self._update_translate_button_size)

    def _populate_language_combo(self, combo, languages, default_code):
        combo.blockSignals(True)
        combo.clear()
        for code, label in languages:
            combo.addItem(label, code)

        default_index = combo.findData(default_code)
        combo.setCurrentIndex(default_index if default_index >= 0 else 0)
        combo.blockSignals(False)

    def get_source_language(self):
        return self.source_combo.currentData()

    def get_destination_language(self):
        return self.destination_combo.currentData()

    def set_selected_languages(self, source_language, destination_language):
        self.source_combo.blockSignals(True)
        self.destination_combo.blockSignals(True)

        source_index = self.source_combo.findData(source_language)
        if source_index >= 0:
            self.source_combo.setCurrentIndex(source_index)

        destination_index = self.destination_combo.findData(destination_language)
        if destination_index >= 0:
            self.destination_combo.setCurrentIndex(destination_index)

        self.source_combo.blockSignals(False)
        self.destination_combo.blockSignals(False)
        self._update_reverse_button_state()

    def get_source_text(self):
        return self.translate_src_text.toPlainText()

    def set_input_text(self, text):
        self.translate_src_text.setPlainText(text or "Copy text to populate this field.")
        self.source_scroll.verticalScrollBar().setValue(0)
        self.destination_scroll.verticalScrollBar().setValue(0)

    def set_translated_text(self, translated_text):
        self.translated_text.setText(translated_text or "Translation output will appear here.")
        self.destination_scroll.verticalScrollBar().setValue(
            self.source_scroll.verticalScrollBar().value()
        )

    def set_text(self, text, translated_text):
        self.set_input_text(text)
        self.set_translated_text(translated_text)

    def _reverse_languages(self):
        if self.get_source_language() == "auto":
            return
        source_language = self.get_source_language()
        destination_language = self.get_destination_language()
        self.set_selected_languages(destination_language, source_language)
        self._emit_language_settings()

    def _update_reverse_button_state(self):
        self.reverse_language_button.setEnabled(self.get_source_language() != "auto")

    def _handle_language_change(self):
        self._update_reverse_button_state()
        self._emit_language_settings()

    def _emit_language_settings(self):
        self.languageSettingsChanged.emit(
            self.get_source_language(),
            self.get_destination_language(),
        )
