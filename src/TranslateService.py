from googletrans import Translator
from googletrans import LANGUAGES
from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

class GoogleTranslateService(QObject):
    translationCompleted = Signal(str, str)
    
    def __init__(self):
        super().__init__()

    def get_source_languages(self):
        languages = [("auto", "Auto Detect")]
        languages.extend(self.get_destination_languages())
        return languages

    def get_destination_languages(self):
        return [
            (code, name.title())
            for code, name in sorted(LANGUAGES.items(), key=lambda item: item[1])
        ]

    @asyncSlot(str, str, str)
    async def translate_text(self, src_text, src='auto', dest='en'):
        async with Translator() as translator:
            result = await translator.translate(src_text, src=src, dest=dest)
            self.translationCompleted.emit(src_text, result.text)
