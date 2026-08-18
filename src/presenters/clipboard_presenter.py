import time
import hashlib
from core.clip_data import ClipData
from core.data_mapper import DataMapper
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
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
        self.view.searchRequested.connect(self.handle_search_request)
        self.show_window_callback = show_window_callback
        self.translate_presenter = None
        self.ai_presenter = None
        self._last_signature = None
        self.t1 = time.perf_counter()

    def handle_search_request(self, query: str):
        query = query.strip()
        clips = self.model.search(query) if query else self.model.list_clips()
        self.view.populate_clipboard_list(clips)

    def handle_copy_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier:
            clip_data = DataMapper.to_plain_text(clip_data)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=False)
            self.handle_clipboard_change(clip_data.mime_data, save_to_db=False)

    def handle_paste_request(self, database_id):
        db_row = self.model.get_clip(database_id, full_content=True)
        clip_data = ClipData.from_database(db_row)
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier:
            clip_data = DataMapper.to_plain_text(clip_data)
        if clip_data:
            self.clipboard_service.set_clipboard(clip_data.mime_data, trigger_paste=True)

    def handle_fav_request(self, id):
        moved = self.model.move_row_to(self.model.base.FAVS_SCHEMA_NAME, id)
        if moved:
            self.view.delete_list_item(id)
        else:
            logger.error(f"Failed to move item {id} to favorites")
    
    def clipboard_signature(self, clip_data):
        """Build a stable signature without decoding clipboard content again."""
        if clip_data is None or clip_data.data_bytes is None:
            return None
        return (
            clip_data.mime_type.value,
            hashlib.sha256(bytes(clip_data.data_bytes)).digest(),
        )

    def handle_clipboard_change(self, mime_data, save_to_db: bool = True):
        if not mime_data or not mime_data.formats():
            return

        t2 = time.perf_counter()
        duration = t2 - self.t1
        self.t1 = t2
        double_copy =  0.1 <= duration <= 1.0 # Skip if duration is too short (system fluctuations) or too long
        # Convert once and reuse the result for deduplication. Previously images
        # were decoded here and again below, producing duplicate libpng errors.
        clip_data = ClipData.from_qmime(mime_data)
        signature = self.clipboard_signature(clip_data)
        if signature is None:
            return
        if signature == self._last_signature and not double_copy:
            return
        self._last_signature = signature

        if clip_data is None or clip_data.data is None:
            return

        if (double_copy or not save_to_db) and clip_data.is_text_like() and self.translate_presenter:
            clip_data_tr = DataMapper.to_plain_text(clip_data)
            text_data = clip_data_tr.data
            self.translate_presenter.update_input_text(text_data)
            logger.debug(f"Translate input updated for: {text_data[:50]}...")
    
        if (double_copy or not save_to_db) and self.ai_presenter:
            if clip_data.is_text_like():
                clip_data_ai = DataMapper.to_plain_text(clip_data)
            else:
                clip_data_ai = clip_data
            self.ai_presenter.update_clipdata_preview(clip_data_ai)
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

        if clip_data.mime_type and clip_id:
            if self.view.current_search_query():
                self.handle_search_request(self.view.current_search_query())
            else:
                db_row = self.model.get_clip(clip_id, full_content=False)
                clip_data = ClipData.from_database(db_row)
                self.view.add_list_item(clip_id, clip_data)
                clip_data.delete_full_data()
            

    def clear_clipboard(self):
        self.model.delete_all()
        self.view.clear_list()

    def refresh_view(self):
        self.handle_search_request("")
