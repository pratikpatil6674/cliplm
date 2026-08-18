from PySide6.QtCore import QObject, Signal


class AIPresenter(QObject):
    textPromptRequested = Signal(str, str)
    imagePromptRequested = Signal(str, str)

    def __init__(self, ai_service, view):
        super().__init__()
        self.ai_service = ai_service
        self.ai_service.aiCompleted.connect(self.refresh_view)
        self.ai_service.aiFailed.connect(self.handle_error)
        self.textPromptRequested.connect(self.ai_service.send_text_prompt)
        self.imagePromptRequested.connect(self.ai_service.send_image_prompt)
        self.view = view
        self.last_clip_data = None
        self.show_model_identity()

    def handle_clipdata(self, clip_data):
        self.last_clip_data = clip_data
        if not self.view.is_ai_enabled():
            return

        prompt_text = self.view.get_selected_prompt()
        if not prompt_text:
            self.show_model_identity()
            self.view.set_ai_output("Click a prompt to run it.")
            return

        self.set_input_view(prompt_text, clip_data)
        self.view.set_ai_output("")
        if clip_data.is_text_like():
            self.view.set_request_status(self._request_status("copied text"))
            self.textPromptRequested.emit(prompt_text, clip_data.data)
        elif clip_data.is_image_like():
            self.view.set_request_status(self._request_status("copied image"))
            self.imagePromptRequested.emit(prompt_text, clip_data.image_b64)
        else:
            self.show_model_identity()
            self.view.set_ai_output("This clipboard format cannot be sent to AI.")

    def execute_selected_prompt(self):
        if self.last_clip_data is None:
            self.view.clear_input_data()
            self.show_model_identity()
            self.view.set_ai_output("Copy text or an image first.")
            return
        self.handle_clipdata(self.last_clip_data)

    def update_clipdata_preview(self, clip_data):
        self.last_clip_data = clip_data
        preview_widget = clip_data.create_preview_widget()
        if preview_widget:
            self.view.set_input_data(
                preview_widget,
                self._input_summary(clip_data),
            )
        else:
            self.view.clear_input_data()
        self.show_model_identity()
        self.view.set_ai_output("Click a prompt to run it.")

    def set_input_view(self, prompt_text, clip_data):
        self.view.set_prompt(prompt_text)
        preview_widget = clip_data.create_preview_widget()
        if preview_widget:
            self.view.set_input_data(
                preview_widget,
                self._input_summary(clip_data),
            )
        else:
            self.view.clear_input_data()

    def refresh_view(self, _prompt, ai_result):
        self.view.set_request_status(self._completion_status("Complete"))
        self.view.set_ai_output(ai_result)

    def handle_error(self, message):
        self.view.set_request_status(self._completion_status("Failed"))
        self.view.set_ai_output(f"AI request failed: {message}")

    def show_model_identity(self):
        self.view.set_request_status(
            f"· {self._model_identity()}",
            request_active=False,
        )

    def _model_identity(self):
        profile_name = self.ai_service.profile_name or "LLM"
        model = self.ai_service.model or "model not configured"
        return f"{profile_name} / {model}"

    def _request_status(self, input_description):
        return (
            f"· Sending {input_description} to "
            f"{self._model_identity()}"
        )

    def _completion_status(self, state):
        return f"· {self._model_identity()} · {state}"

    @staticmethod
    def _input_summary(clip_data):
        if clip_data.is_text_like():
            text = str(clip_data.data or "")
            content_type = getattr(clip_data.mime_type, "value", "text")
            label = "HTML" if content_type == "html" else "Text"
            single_line = " ".join(text.split())
            details = f"{label} · {len(text):,} characters"
            return f"{details} · {single_line}" if single_line else details

        if clip_data.is_image_like() and clip_data.data is not None:
            return f"Image · {clip_data.data.width()} × {clip_data.data.height()}"

        data = clip_data.data
        if isinstance(data, list):
            return f"URLs · {len(data)} item(s)"
        return "Copied input"
