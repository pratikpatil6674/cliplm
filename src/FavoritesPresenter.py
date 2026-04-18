from ClipData import ClipData
import logging

logger = logging.getLogger(__name__)

class IFavoritesPresenter:
    def handle_copy_request(self, database_id):
        ...
    def handle_paste_request(self, database_id):
        ...
    def clear_clipboard(self):
        ...

class FavoritesPresenter():
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.model = model 
        self.view = view

    def handle_copy_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=False)

    def handle_paste_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=True)
        
    def handle_fav_request(self, id):
        # ID is received from clipboard tab list item
        clip = self.model.get_clip(id)
        if clip is None:
            logger.warning(f"Clip with id {id} not found in favourites db table")
            return
        clip_data = ClipData.from_database(clip)
        # breakpoint()
        self.view.add_list_item(clip['clip_id'], clip_data)

    def handle_delete_request(self, id):
        self.model.delete_clip(id)
        self.view.delete_list_item(id)
        
    def refresh_view(self):
        clips = self.model.list_clips()
        self.view.populate_fav_list(clips)