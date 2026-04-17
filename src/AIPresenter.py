
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

class AIPresenter(QObject):
    textPromptRequested = Signal(str, str)
    imagePromptRequested = Signal(str, str)
    def __init__(self, ai_service, view):
        super().__init__()
        self.ai_service = ai_service
        self.ai_service.aiCompleted.connect(self.refresh_view)
        self.textPromptRequested.connect(self.ai_service.send_text_prompt)
        self.imagePromptRequested.connect(self.ai_service.send_image_prompt)
        self.view = view
        self.last_clip_data = None
    
    def handle_clipdata(self, clip_data):
        self.last_clip_data = clip_data
        if not self.view.is_ai_enabled():
            return
        prompt_text = self.view.get_selected_prompt()
        if not prompt_text:
            self.view.set_ai_output("Select a prompt to run.")
            return
        self.set_input_view(prompt_text,clip_data)
        self.view.set_ai_output("Waiting for response...")
        if clip_data.is_text_like():
            self.textPromptRequested.emit(prompt_text, clip_data.data)
        elif clip_data.is_image_like():
            self.imagePromptRequested.emit(prompt_text, clip_data.image_b64)

    def execute_selected_prompt(self):
        # if not self.view.is_ai_enabled():
        #     self.view.set_ai_output("Enable AI to run a prompt.")
        #     return
        if self.last_clip_data is None:
            self.view.set_ai_output("Copy text or an image first.")
            return
        self.handle_clipdata(self.last_clip_data)

    def update_clipdata_preview(self, clip_data):
        self.last_clip_data = clip_data
        self.view.set_prompt(self.view.get_selected_prompt())
        preview_widget = clip_data.create_preview_widget()
        if preview_widget:
            self.view.set_input_data(preview_widget)
        self.view.set_ai_output("Select a prompt to run.")
    
    def set_input_view(self, prompt_text, clip_data):
        self.view.set_prompt(prompt_text)
        preview_widget = clip_data.create_preview_widget()
        print(f"Preview widget: {preview_widget}, data is {clip_data.data}")
        if preview_widget:
            self.view.set_input_data(preview_widget)
        else:
            print(f"No preview widget available for clip data: {clip_data.mime_type}")

    def refresh_view(self, prompt, ai_result):
        print(f"AI view refreshed: {prompt} -> {ai_result}")
        self.view.set_ai_output(ai_result)
