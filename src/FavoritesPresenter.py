
class IFavoritesPresenter:
    def handle_copy_request(self, text):
        ...
    def handle_paste_request(self, text):
        ...
    def clear_clipboard(self):
        ...

class FavoritesPresenter():
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.model = model 
        self.view = view

    def handle_copy_request(self, text):
        self.clipboard_service.copy_text(text)

    def handle_paste_request(self, text):
        self.clipboard_service.paste_text(text)

    def handle_fav_request(self, id, text):
        # ID is received from clipboard tab list item
        self.model.add(id, text)
        self.view.add_list_item(id, text)

    def handle_delete_request(self, id):
        self.model.delete(id)
        self.view.delete_list_item(id)
        
    def refresh_view(self):
        self.view.populate_fav_list(self.model.get_all())