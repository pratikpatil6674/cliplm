"""Lazy full-content adapter for lightweight database rows."""

from typing import Any, Dict, Optional


class DatabaseRecord:
    """Resolve full clip content only when a consumer asks for it."""

    def __init__(self, db_row, table):
        self.db_row = db_row
        self.table = table

    def get_full_content(self) -> Optional[Dict[str, Any]]:
        return self.table.get_clip(self.db_row["clip_id"], full_content=True)
