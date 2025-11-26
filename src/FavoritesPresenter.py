from ClipData import ClipData

class IFavoritesPresenter:
    def handle_copy_request(self, qmime_data):
        ...
    def handle_paste_request(self, qmime_data):
        ...
    def clear_clipboard(self):
        ...

class FavoritesPresenter():
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.model = model 
        self.view = view

    def handle_copy_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=False)

    def handle_paste_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=True)
        
    def handle_fav_request(self, id):
        # ID is received from clipboard tab list item
        clip = self.model.get_clip(id)
        clip_data = ClipData.from_database(clip)
        self.view.add_list_item(clip['clip_id'], clip_data)

    def handle_delete_request(self, id):
        self.model.delete_clip(id)
        self.view.delete_list_item(id)
        
    def refresh_view(self):
        clips = self.model.list_clips()
        self.view.populate_fav_list(clips)