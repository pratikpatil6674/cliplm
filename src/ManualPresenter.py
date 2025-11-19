from JsonDB import ManualDB

class ManualPresenter:
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.model = model
        self.view = view
        self.view.addRequested.connect(self.handle_add_request)
    
    def handle_delete_request(self, id):
        self.model.delete(id)
        self.refresh_view()
    
    def handle_add_request(self):
        title, text = self.view.get_manual_entry()
        if title and text:
            self.model.add(title, text)
            self.refresh_view()

    def handle_edit_request(self, id, title, text):
        title, text = self.view.get_manual_entry(title, text)
        if title and text:
            self.model.edit(id, title, text)
            self.refresh_view()

    def handle_copy_request(self, text):
        self.clipboard_service.copy_text(text)

    def handle_paste_request(self, text):
        self.clipboard_service.paste_text(text)


    def refresh_view(self):
        self.view.populate_manual_list(self.model.get_all())