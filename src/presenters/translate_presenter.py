from PySide6.QtCore import QObject, Signal


class TranslatePresenter(QObject):
    translationRequested = Signal(str, str, str)

    def __init__(self, translate_service, view):
        super().__init__()
        self.translate_service = translate_service
        self.translate_service.translationCompleted.connect(self.refresh_view)
        self.translationRequested.connect(self.translate_service.translate_text)
        self.view = view
        self.view.translateRequested.connect(self.handle_translate_request)
        self._load_languages()

    def _load_languages(self):
        source_languages = self.translate_service.get_source_languages()
        destination_languages = self.translate_service.get_destination_languages()
        self.view.set_language_options(source_languages, destination_languages)

    def update_input_text(self, src_text):
        self.view.set_input_text(src_text or "")

    def handle_translate_request(self):
        src_text = self.view.get_source_text()
        if not src_text:
            self.view.set_translated_text("Copy text first.")
            return

        source_language = self.view.get_source_language()
        destination_language = self.view.get_destination_language()
        self.view.set_translated_text("Translating...")
        self.translationRequested.emit(src_text, source_language, destination_language)

    def refresh_view(self, src_text, translated_text):
        self.view.set_text(src_text, translated_text)
