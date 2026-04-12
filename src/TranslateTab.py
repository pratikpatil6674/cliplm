from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TranslateTab(QWidget):
    translateRequested = Signal()
    languageSettingsChanged = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._language_items = []
        self._setup_ui()
        self._setup_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        controls = QFrame()
        controls.setObjectName("controls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        controls_layout.setSpacing(8)

        self.source_label = QLabel("Source")
        self.source_label.setObjectName("section_label")
        controls_layout.addWidget(self.source_label)

        self.source_combo = QComboBox()
        self.source_combo.setObjectName("language_combo")
        self.source_combo.currentIndexChanged.connect(self._emit_language_settings)
        controls_layout.addWidget(self.source_combo, 1)

        self.destination_label = QLabel("Target")
        self.destination_label.setObjectName("section_label")
        controls_layout.addWidget(self.destination_label)

        self.destination_combo = QComboBox()
        self.destination_combo.setObjectName("language_combo")
        self.destination_combo.currentIndexChanged.connect(self._emit_language_settings)
        controls_layout.addWidget(self.destination_combo, 1)

        self.translate_button = QPushButton("Translate")
        self.translate_button.setObjectName("translate_button")
        self.translate_button.setCursor(Qt.PointingHandCursor)
        self.translate_button.clicked.connect(self.translateRequested.emit)
        controls_layout.addWidget(self.translate_button)

        layout.addWidget(controls)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(6)

        self.input_label = QLabel("Input Text")
        self.input_label.setObjectName("section_label")
        card_layout.addWidget(self.input_label)

        self.translate_src_text = QLabel("Copy text to populate this field.")
        self.translate_src_text.setObjectName("translate_src_text")
        self.translate_src_text.setTextFormat(Qt.PlainText)
        self.translate_src_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translate_src_text.setWordWrap(True)
        self.translate_src_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll1 = QScrollArea()
        scroll1.setWidgetResizable(True)
        scroll1.setWidget(self.translate_src_text)
        card_layout.addWidget(scroll1)

        self.output_label = QLabel("Translated Text")
        self.output_label.setObjectName("section_label")
        card_layout.addWidget(self.output_label)

        self.translated_text = QLabel("Translation output will appear here.")
        self.translated_text.setObjectName("translated_text")
        self.translated_text.setTextFormat(Qt.PlainText)
        self.translated_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.translated_text.setWordWrap(True)
        self.translated_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setWidget(self.translated_text)
        card_layout.addWidget(scroll2)

        layout.addWidget(card)

    def _setup_styles(self):
        self.setStyleSheet(
            """
            QWidget { background: #f5f7fb; color: #1f2933; }
            QFrame#controls, QFrame#card {
                background: #ffffff;
                border-radius: 10px;
                border: 1px solid rgba(30,36,44,0.06);
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
                border-radius: 8px;
                border: 1px solid rgba(20,24,30,0.06);
                background: white;
                font-size: 13px;
            }
            QPushButton#translate_button {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
                color: #fff;
                border: none;
                padding: 8px 10px;
                border-radius: 8px;
                text-transform: none;
                font-weight: 600;
                font-family: Ubuntu, sans-serif;
                font-size: 14px;
            }
            QPushButton#translate_button:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
            }
            QLabel#translate_src_text, QLabel#translated_text {
                color: #263238;
                margin: 0;
                border: 1px solid rgba(30,36,44,0.06);
                padding: 8px 10px;
                background: #fbfdff;
                border-radius: 8px;
            }
            QLabel#translated_text {
                background: #ffffff;
            }
        """
        )

    def set_language_options(self, source_languages, destination_languages):
        self._language_items = list(destination_languages)
        self._populate_language_combo(self.source_combo, source_languages, "auto")
        self._populate_language_combo(self.destination_combo, destination_languages, "en")

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

    def get_source_text(self):
        return self.translate_src_text.text()

    def set_input_text(self, text):
        self.translate_src_text.setText(text or "Copy text to populate this field.")

    def set_translated_text(self, translated_text):
        self.translated_text.setText(translated_text or "Translation output will appear here.")

    def set_text(self, text, translated_text):
        self.set_input_text(text)
        self.set_translated_text(translated_text)

    def _emit_language_settings(self):
        self.languageSettingsChanged.emit(
            self.get_source_language(),
            self.get_destination_language(),
        )
