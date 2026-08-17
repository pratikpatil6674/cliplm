"""Application-facing facade over ClipLM database repositories."""

from .clipboard_repository import ClipboardTable
from .connection import BaseDB
from .notes_repository import NotesTable


class ClipboardStore:
    """
    Expose related repositories through one lifecycle-managed Facade.

    Callers do not construct connections or know table names. Repositories
    share one BaseDB so cross-bucket moves remain transactional.
    """

    def __init__(self, db_path: str, data_dir: str):
        self.base = BaseDB(db_path, data_dir)
        self.clipboard = ClipboardTable(self.base, BaseDB.CLIP_SCHEMA_NAME)
        self.favourites = ClipboardTable(self.base, BaseDB.FAVS_SCHEMA_NAME)
        self.notes = NotesTable(self.base)

    def move_to_favourites(self, clip_id: str) -> bool:
        return self.clipboard.move_row_to(BaseDB.FAVS_SCHEMA_NAME, clip_id)

    def move_to_clipboard(self, clip_id: str) -> bool:
        return self.favourites.move_row_to(BaseDB.CLIP_SCHEMA_NAME, clip_id)

    def close(self) -> None:
        self.base.close()
