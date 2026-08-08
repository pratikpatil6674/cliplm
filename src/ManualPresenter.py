from ClipData import ClipData

class ManualPresenter:
    def __init__(self, clipboard_service, model, view):
        self.clipboard_service = clipboard_service
        self.model = model
        self.view = view
        self.view.addRequested.connect(self.handle_add_request)
        self.view.searchRequested.connect(self.handle_search_request)
    
    def handle_search_request(self, query: str):
        query = query.strip()
        notes = self.model.search_notes(query) if query else self.model.list_notes()
        self.view.populate_manual_list(notes)

    def handle_delete_request(self, id):
        self.model.delete_note(id)
        self.view.delete_list_item(id)
    
    def handle_add_request(self):
        # breakpoint()
        title, text = self.view.get_manual_entry()
        print(f"Adding manual entry: title='{title}', text='{text}'")
        if title and text:
            note_id = self.model.add_note(title, text)
            if self.view.current_search_query():
                self.handle_search_request(self.view.current_search_query())
                return
            note = self.model.get_note(note_id)
            print(f"Note added with ID: {note_id}")
            print(f"Note data: {note}")
            clip_data_top = ClipData.from_database(note, data_key='title')
            clip_data_bottom = ClipData.from_database(note, data_key='preview_text')
            self.view.add_list_item(note_id, clip_data_top, clip_data_bottom)


    def handle_edit_request(self, id):
        note = self.model.get_note(id)
        if not note:
            return
        title, text = self.view.get_manual_entry(note['title'], note['preview_text'])
        if title and text:
            updated_note = self.model.update_note(id, title, text)
            if self.view.current_search_query():
                self.handle_search_request(self.view.current_search_query())
            else:
                self.view.add_list_item(
                    id,
                    ClipData.from_database(updated_note, data_key='title'),
                    ClipData.from_database(updated_note, data_key='preview_text'),
                )

    def handle_copy_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=False)

    def handle_paste_request(self, qmime_data):
        self.clipboard_service.set_clipboard(qmime_data, trigger_paste=True)


    def refresh_view(self):
        self.handle_search_request("")
