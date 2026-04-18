import time
import os
from ClipData import ClipData
import logging
logger=logging.getLogger(__name__)

class IClipboardPresenter:
    def handle_copy_request(self, database_id):
        ...
    def handle_paste_request(self, database_id):
        ...
    def clear_clipboard(self):
        ...

class ClipboardPresenter(IClipboardPresenter):
    def __init__(self, clipboard_service, model, view, show_window_callback):
        self.clipboard_service = clipboard_service
        self.clipboard_service.clipboardChanged.connect(self.handle_clipboard_change)
        self.model = model 
        self.view = view
        self.view.clearRequested.connect(self.clear_clipboard)
        self.show_window_callback = show_window_callback
        self.translate_presenter = None
        self.ai_presenter = None
        
        self.t1 = time.perf_counter()

    def handle_copy_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=False)
            self.handle_clipboard_change(clip_data.mime_data, save_to_db=False)

    def handle_paste_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=True)

    def handle_fav_request(self, id):
        moved = self.model.move_row_to(self.model.base.FAVS_SCHEMA_NAME, id)
        if moved:
            self.view.delete_list_item(id)
        else:
            logger.error(f"Failed to move item {id} to favorites")

    def handle_clipboard_change(self, mime_data, save_to_db: bool = True):
        clip_data = ClipData.from_qmime(mime_data)
        if clip_data.data is None:
            return
        
        t2 = time.perf_counter()
        duration = t2 - self.t1
        self.t1 = t2
        if (duration < 1.0 or not save_to_db) and clip_data.is_text_like() and self.translate_presenter:
            text_data = clip_data.data
            self.translate_presenter.update_input_text(text_data)
            logger.debug(f"Translate input updated for: {text_data[:50]}...")
    
        if (duration < 1.0 or not save_to_db) and self.ai_presenter:
            self.ai_presenter.update_clipdata_preview(clip_data)
            if save_to_db:
                self.show_window_callback(tab_index=4)
            return
        
        # User may not be able to capture the image in 1 second, so always set AI input for images
        if clip_data.is_image_like() and self.ai_presenter:
            self.ai_presenter.update_clipdata_preview(clip_data)
        
        if not save_to_db:
            return
            
        clip_id = self.model.add_clip(
            clip_data.data_bytes,
            clip_data.mime_type,
            preview_text=clip_data.preview_text,
            thumbnail_bytes=clip_data.preview_bytes
        )
        # if clip_id:
        #     clip_data.database_id = clip_id

        if clip_data.mime_type:
            db_row = self.model.get_clip(clip_id, full_content=False)
            clip_data = ClipData.from_database(db_row)
            self.view.add_list_item(clip_id, clip_data)
            clip_data.delete_full_data()
            

    def clear_clipboard(self):
        self.model.delete_all()
        self.view.clear_list()

    def refresh_view(self):
        clips = self.model.list_clips()
        self.view.populate_clipboard_list(clips)
