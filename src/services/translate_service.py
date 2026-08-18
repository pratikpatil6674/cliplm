from googletrans import LANGUAGES
from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

from .translation_providers import (
    GoogleTranslationProvider,
    LLMTranslationProvider,
    TranslationProvider,
)

class TranslateService(QObject):
    """Select a translation Strategy and publish results through Qt signals."""

    translationCompleted = Signal(str, str)
    
    def __init__(self, llm_service=None):
        super().__init__()
        self.llm_service = llm_service
        self.provider = "google"
        self._providers: dict[str, TranslationProvider] = {
            "google": GoogleTranslationProvider(),
            "llm": LLMTranslationProvider(llm_service),
        }

    def get_source_languages(self):
        languages = [("auto", "Auto Detect")]
        languages.extend(self.get_destination_languages())
        return languages

    def get_destination_languages(self):
        return [
            (code, name.title())
            for code, name in sorted(LANGUAGES.items(), key=lambda item: item[1])
        ]

    def configure(self, provider="google", llm_service=None):
        self.provider = provider or "google"
        if llm_service is not None:
            self.llm_service = llm_service
            self._providers["llm"] = LLMTranslationProvider(llm_service)

    @asyncSlot(str, str, str)
    async def translate_text(self, src_text, src="auto", dest="en"):
        strategy = self._providers.get(self.provider, self._providers["google"])
        translated_text = await strategy.translate(src_text, src, dest)
        self.translationCompleted.emit(src_text, translated_text)
