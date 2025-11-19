from ClipData import ClipData
class IClipboardPresenter:
    def handle_copy_request(self, text):
        ...
    def handle_paste_request(self, text):
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

    def handle_copy_request(self, text):
        self.clipboard_service.copy_text(text)

    def handle_paste_request(self, text):
        print("paste request ", id(text))
        self.clipboard_service.paste_text(text)

    def handle_fav_request(self, id):
        self.model.delete(id)
        self.view.delete_list_item(id)
        self.refresh_view()

    def handle_clipboard_change(self, mime_data):
        if self.translate_presenter:
            self.translate_presenter.translate_text(mime_data)

        id = self.model.add(text)
        print("clipboard change mime data -> data", mime_data.formats(), mime_data.data("text/plain"))
        clip_data = ClipData(mime_data)
        if clip_data.mime_type:
            self.view.add_list_item(id, clip_data)
        self.refresh_view()

    def clear_clipboard(self):
        self.model.delete_all()
        self.view.clear_list()
        # self.refresh_view()

    def refresh_view(self):
        self.view.populate_clipboard_list(self.model.get_all())