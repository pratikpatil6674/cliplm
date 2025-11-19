import asyncio
from PySide6.QtCore import QThreadPool
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

class TranslatePresenter(QObject):
    translationRequested = Signal(str)
    def __init__(self, translate_service, view):
        super().__init__()
        self.translate_service = translate_service
        self.translate_service.translationCompleted.connect(self.refresh_view)
        self.translationRequested.connect(self.translate_service.translate_text)
        self.view = view
    
    def translate_text(self, src_text):
        if self.view.is_translate_enabled():
            self.translationRequested.emit(src_text)
            # translated_text = self.translate_service.request_translation_in_process(src_text) 
            # self.refresh_view(src_text, translated_text)

    def refresh_view(self, src_text, translated_text):
        self.view.set_text(src_text, translated_text)