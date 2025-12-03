import time
import os
from ClipData import ClipData
class IClipboardPresenter:
    def handle_copy_request(self, qmime_data):
        ...
    def handle_paste_request(self, qmime_data):
        ...
    def clear_clipboard(self):
        ...

class ClipboardPresenter(IClipboardPresenter):
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.clipboard_service.clipboardChanged.connect(self.handle_clipboard_change)
        self.model = model 
        self.view = view
        self.view.clearRequested.connect(self.clear_clipboard)
        self.translate_presenter = None
        self.ai_presenter = None

    def handle_copy_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=False)

    def handle_paste_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=True)

    def handle_fav_request(self, id):
        self.model.move_row_to(self.model.base.FAVS_SCHEMA_NAME, id)
        self.view.delete_list_item(id)

    def handle_clipboard_change(self, mime_data):
        if self.translate_presenter and self.translate_presenter.view.is_translate_enabled():
            text_data = mime_data.data("text/plain").data().decode('utf-8')
            self.translate_presenter.translate_text(text_data)
            print(f"translate triggered for: {text_data}")
            return
        if self.ai_presenter and self.ai_presenter.view.is_ai_enabled():
            text_data = mime_data.data("text/plain").data().decode('utf-8')
            self.ai_presenter.process_text(text_data)
            print(f"AI processing triggered for: {text_data}")
            return
        clip_data = ClipData.from_qmime(mime_data)
        clip_id = self.model.add_clip(clip_data.bytes_data, clip_data.mime_type)
        # print(f"clipboard change mime data -> data, id: {clip_id}", mime_data.formats(), mime_data.data("text/plain"))
        if clip_data.mime_type:
            self.view.add_list_item(clip_id, clip_data)

    def clear_clipboard(self):
        self.model.delete_all()
        self.view.clear_list()

    def refresh_view(self):
        clips = self.model.list_clips()
        self.view.populate_clipboard_list(clips)