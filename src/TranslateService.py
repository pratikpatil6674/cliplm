from googletrans import Translator
from googletrans import LANGUAGES
from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

class TranslateService(QObject):
    translationCompleted = Signal(str, str)
    
    def __init__(self, llm_service=None):
        super().__init__()
        self.llm_service = llm_service
        self.provider = "google"

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

    @asyncSlot(str, str, str)
    async def translate_text(self, src_text, src='auto', dest='en'):
        if self.provider == "llm":
            translated_text = await self._translate_with_llm(src_text, src, dest)
        else:
            translated_text = await self._translate_with_google(src_text, src, dest)

        self.translationCompleted.emit(src_text, translated_text)

    async def _translate_with_google(self, src_text, src="auto", dest="en"):
        async with Translator() as translator:
            result = await translator.translate(src_text, src=src, dest=dest)
            return result.text

    async def _translate_with_llm(self, src_text, src="auto", dest="en"):
        if (
            self.llm_service is None
            or self.llm_service.client is None
            or not self.llm_service.model
        ):
            return "LLM API is not configured. Select a default LLM profile in Settings."

        source_label = self._language_label(src, allow_auto=True)
        destination_label = self._language_label(dest)
        prompt = (
            f"Translate the following text from {source_label} to {destination_label}.\n"
            "Return only the translated text. Do not add explanation, notes, or quotes.\n\n"
            f"{src_text}"
        )
        return await self.llm_service.complete_text(prompt)

    def _language_label(self, code, allow_auto=False):
        if allow_auto and code == "auto":
            return "the automatically detected source language"
        return LANGUAGES.get(code, code).title()
