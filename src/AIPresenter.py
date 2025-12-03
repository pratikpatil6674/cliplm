import asyncio
from PySide6.QtCore import QThreadPool
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

class AIPresenter(QObject):
    aiRequested = Signal(str, str)
    def __init__(self, ai_service, view):
        super().__init__()
        self.ai_service = ai_service
        self.ai_service.aiCompleted.connect(self.refresh_view)
        self.aiRequested.connect(self.ai_service.send_text_prompt)
        self.view = view
    
    def process_text(self, data_text):
        if self.view.is_ai_enabled():
            prompt_text = self.view.get_selected_prompt()
            self.view.set_prompt(prompt_text)
            self.view.set_input_data(data_text)
            print(f"AI processing requested for: {data_text}")
            self.aiRequested.emit(prompt_text, data_text)

    def refresh_view(self, prompt, ai_result):
        print(f"AI view refreshed: {prompt} -> {ai_result}")
        self.view.set_ai_output(ai_result)