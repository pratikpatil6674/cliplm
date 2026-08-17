"""Repository for user-created text notes."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .connection import BaseDB
from .utils import iso_now


class NotesTable:
    """Keep note SQL and row mapping behind a small Repository interface."""

    def __init__(self, base: BaseDB):
        self.base = base
        self._execute = base._execute
        self.json_dumps = base.json_dumps
        self.json_loads = base.json_loads
        self._lock = base._lock

    def add_note(self, title: str, main_text: str, tags: Optional[List[str]] = None) -> str:
        note_id = str(uuid.uuid4())
        now = iso_now()
        self._execute(
            """
            INSERT INTO text_notes (
                note_id, content_type, title, main_text, preview_text,
                tags, created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (note_id, "text", title, main_text, main_text,
             self.json_dumps(tags or []), now, now),
            commit=True,
        )
        return note_id

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        row = self._execute(
            "SELECT * FROM text_notes WHERE note_id = ?;", (note_id,)
        ).fetchone()
        if not row:
            return None
        note = dict(row)
        note["tags"] = self.json_loads(note.get("tags"))
        return note

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        main_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        note = self.get_note(note_id)
        if not note:
            return False
        title = title if title is not None else note["title"]
        main_text = main_text if main_text is not None else note["main_text"]
        tags_json = self.json_dumps(tags if tags is not None else note.get("tags", []))
        self._execute(
            """
            UPDATE text_notes
            SET title = ?, main_text = ?, preview_text = ?, tags = ?, modified_at = ?
            WHERE note_id = ?;
            """,
            (title, main_text, main_text, tags_json, iso_now(), note_id),
            commit=True,
        )
        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        cursor = self._execute(
            "DELETE FROM text_notes WHERE note_id = ?;", (note_id,), commit=True
        )
        return cursor.rowcount > 0

    def list_notes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        rows = self._execute(
            """
            SELECT note_id, content_type, title, preview_text,
                   created_at, modified_at
            FROM text_notes
            ORDER BY modified_at ASC
            LIMIT ? OFFSET ?;
            """,
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def search_notes(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return self.list_notes(limit=limit)
        like_query = f"%{query}%"
        rows = self._execute(
            """
            SELECT note_id, content_type, title, preview_text,
                   created_at, modified_at
            FROM text_notes
            WHERE title LIKE ? OR main_text LIKE ?
                  OR preview_text LIKE ? OR tags LIKE ?
            ORDER BY modified_at ASC
            LIMIT ?;
            """,
            (like_query, like_query, like_query, like_query, limit),
        ).fetchall()
        return [dict(row) for row in rows]
