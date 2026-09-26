from PySide6.QtCore import QObject, Qt, QTimer, Signal


class AIPresenter(QObject):
    textPromptRequested = Signal(str, str, int)
    imagePromptRequested = Signal(str, str, int)

    def __init__(self, ai_service, view):
        super().__init__()
        self.ai_service = ai_service
        self.ai_service.aiChunk.connect(self.receive_chunk)
        self.ai_service.aiCompleted.connect(self.refresh_view)
        self.ai_service.aiFailed.connect(self.handle_error)
        self.textPromptRequested.connect(self.ai_service.send_text_prompt)
        self.imagePromptRequested.connect(self.ai_service.send_image_prompt)
        self.view = view
        self.last_clip_data = None
        self._request_id = 0
        self._output_parts = []
        self._pending_text = ""
        self._revealed_text = ""
        self._finish_state = None
        self._active_identity = ""
        self._render_timer = QTimer(self)
        self._render_timer.setTimerType(Qt.PreciseTimer)
        self._render_timer.setInterval(25)
        self._render_timer.timeout.connect(self._render_stream)
        self.show_model_identity()

    def handle_clipdata(self, clip_data):
        self.last_clip_data = clip_data
        if not self.view.is_ai_enabled():
            self._invalidate_request()
            return

        prompt_text = self.view.get_selected_prompt()
        if not prompt_text:
            self._invalidate_request()
            self.show_model_identity()
            self.view.set_ai_output("Click a prompt to run it.")
            return

        self.set_input_view(prompt_text, clip_data)
        request_id = self._invalidate_request()
        self._active_identity = self._model_identity()
        self.view.set_ai_output("")
        if clip_data.is_text_like():
            self.view.set_request_status(self._request_status("copied text"))
            self.textPromptRequested.emit(prompt_text, clip_data.data, request_id)
        elif clip_data.is_image_like():
            self.view.set_request_status(self._request_status("copied image"))
            self.imagePromptRequested.emit(prompt_text, clip_data.image_b64, request_id)
        else:
            self.show_model_identity()
            self.view.set_ai_output("This clipboard format cannot be sent to AI.")

    def execute_selected_prompt(self):
        if self.last_clip_data is None:
            self._invalidate_request()
            self.view.clear_input_data()
            self.show_model_identity()
            self.view.set_ai_output("Copy text or an image first.")
            return
        self.handle_clipdata(self.last_clip_data)

    def update_clipdata_preview(self, clip_data):
        self._invalidate_request()
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

    def _invalidate_request(self):
        self._request_id += 1
        self._output_parts = []
        self._pending_text = ""
        self._revealed_text = ""
        self._finish_state = None
        self._render_timer.stop()
        return self._request_id

    def receive_chunk(self, request_id, chunk):
        if request_id != self._request_id:
            return
        self._output_parts.append(chunk)
        self._pending_text += chunk
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _render_stream(self):
        if self._pending_text:
            # Reveal short groups, increasing the group size only for larger bursts.
            count = max(16, min(96, (len(self._pending_text) + 5) // 6))
            self._revealed_text += self._pending_text[:count]
            self._pending_text = self._pending_text[count:]
            self.view.set_ai_output(self._revealed_text)
        if not self._pending_text:
            if self._finish_state is not None:
                self._finish_stream()
            else:
                self._render_timer.stop()

    def _finish_stream(self):
        self._render_timer.stop()
        state, text = self._finish_state
        self._finish_state = None
        self.view.set_request_status(self._completion_status(state))
        self.view.set_ai_output(text)

    def refresh_view(self, request_id, ai_result):
        if request_id != self._request_id:
            return
        self._finish_state = ("Complete", ai_result)
        if not self._pending_text:
            self._finish_stream()

    def handle_error(self, request_id, message):
        if request_id != self._request_id:
            return
        partial = "".join(self._output_parts)
        self._finish_state = (
            "Failed",
            f"{partial}\n\nAI request failed: {message}" if partial
            else f"AI request failed: {message}",
        )
        if not self._pending_text:
            self._finish_stream()

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
        return f"· {self._active_identity or self._model_identity()} · {state}"

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
