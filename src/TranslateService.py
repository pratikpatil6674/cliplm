
from googletrans import Translator
from PySide6.QtCore import QObject, Signal
from qasync import asyncSlot

class GoogleTranslateService(QObject):
    translationCompleted = Signal(str, str)
    
    def __init__(self):
        super().__init__()

    @asyncSlot()    
    async def translate_text(self, src_text, dest='en'):
        async with Translator() as translator:
            result = await translator.translate(src_text, dest=dest)
            self.translationCompleted.emit(src_text, result.text)