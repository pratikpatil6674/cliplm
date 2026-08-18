"""Repository for clipboard and favourite clip buckets."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from core.clip_data import MimeType

from .connection import BaseDB
from .utils import iso_now


logger = logging.getLogger(__name__)


class ClipboardTable:
    """
    Provide clip persistence for one validated clipboard-like table.

    This is the Repository boundary: presenters use domain-oriented methods
    while SQL and row mapping remain inside this class. The shared BaseDB is
    injected so clipboard and favourites participate in the same transactions.
    """

    FILE_ON_DISK_THRESHOLD = 256 * 1024

    def __init__(self, base: BaseDB, table_name: str):
        self._validate_table_name(table_name)
        self.base = base
        self.table = table_name
        self.conn = base.conn
        self._lock = base._lock
        self._execute = base._execute
        self.sha256 = base.sha256
        self.json_dumps = base.json_dumps
        self.json_loads = base.json_loads
        self._path_for_new_file = base._path_for_new_file
        self.rebuild_clip_fts = base.rebuild_clip_fts

    @staticmethod
    def _validate_table_name(name: str) -> None:
        # Table names cannot be SQL parameters. Restrict the injected bucket
        # name before it is used in f-strings.
        if not name or not all(character.isalnum() or character == "_" for character in name):
            raise ValueError("Invalid table name")

    def add_clip(
        self,
        content: bytes,
        mime: str,
        file_name: Optional[str] = None,
        source_app: Optional[str] = None,
        window_title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        save_file_to_disk_if_large: bool = True,
        preview_text: Optional[str] = None,
        thumbnail_bytes: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a clip, deduplicating only within this repository's bucket."""
        content_hash = self.sha256(content)
        now = iso_now()
        tags_json = self.json_dumps(tags or [])
        metadata_json = json.dumps(metadata or {})

        row = self._execute(
            f"SELECT clip_id FROM {self.table} WHERE content_hash = ? LIMIT 1;",
            (content_hash,),
        ).fetchone()
        if row:
            return row["clip_id"]

        clip_id = str(uuid.uuid4())
        size = len(content)
        is_file = 0
        file_path = None
        full_text = None

        if mime and (
            mime.startswith("text")
            or mime.startswith("html")
            or mime.endswith("xml")
            or mime.endswith("json")
        ):
            try:
                full_text = content.decode("utf-8", errors="replace")
            except Exception:
                full_text = None

        if save_file_to_disk_if_large and mime == MimeType.IMAGE:
            extension = None
            if file_name and "." in file_name:
                extension = file_name.split(".")[-1]
            file_path = self._path_for_new_file(extension)
            with open(file_path, "wb") as file:
                file.write(content)
            is_file = 1

        self._execute(
            f"""
            INSERT INTO {self.table} (
                clip_id, content_type, content_size, content_hash,
                is_file, file_path, file_name, thumbnail, preview_text,
                full_text, source_app, window_title, tags, language, metadata,
                created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                clip_id,
                mime,
                size,
                content_hash,
                is_file,
                file_path,
                file_name,
                thumbnail_bytes,
                preview_text,
                full_text,
                source_app,
                window_title,
                tags_json,
                None,
                metadata_json,
                now,
                now,
            ),
            commit=True,
        )

        content_text = " ".join(
            filter(
                None,
                [
                    preview_text or "",
                    full_text or "",
                    file_name or "",
                    " ".join(tags or []),
                ],
            )
        )
        self._execute(
            "INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);",
            (clip_id, content_text),
            commit=True,
        )
        return clip_id

    def get_clip(
        self, clip_id: str, full_content: bool = False
    ) -> Optional[Dict[str, Any]]:
        row = self._execute(
            f"SELECT * FROM {self.table} WHERE clip_id = ?;", (clip_id,)
        ).fetchone()
        if not row:
            return None

        record = dict(row)
        record["tags"] = self.json_loads(record.get("tags"))
        try:
            record["metadata"] = json.loads(record.get("metadata") or "{}")
        except Exception:
            record["metadata"] = {}

        mime_type = record["content_type"]
        if mime_type == MimeType.IMAGE:
            record["content"] = record["thumbnail"] if not full_content else None
            record["full_text"] = None
            if full_content and record.get("is_file"):
                try:
                    with open(record.get("file_path"), "rb") as file:
                        record["content"] = file.read()
                except Exception:
                    record["content"] = None
        elif mime_type in (MimeType.TEXT, MimeType.HTML):
            record["content"] = (
                record["full_text"] if full_content else record["preview_text"]
            )
        return record

    def list_clips(
        self,
        limit: int = 10000,
        offset: int = 0,
        order_by: str = "created_at ASC",
    ) -> List[Dict[str, Any]]:
        rows = self._execute(
            f"""
            SELECT clip_id, content_type, content_size, preview_text, thumbnail,
                   created_at, source_app, file_name
            FROM {self.table}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?;
            """,
            (limit, offset),
        ).fetchall()
        return self._rows_to_previews(rows)

    @staticmethod
    def _rows_to_previews(rows) -> List[Dict[str, Any]]:
        """Map database rows to the lightweight shape expected by card views."""
        result = []
        for row in rows:
            record = dict(row)
            if record["content_type"] == MimeType.IMAGE:
                record["content"] = record["thumbnail"]
            elif record["content_type"] in (MimeType.TEXT, MimeType.HTML):
                record["content"] = record["preview_text"]
            result.append(record)
        return result

    def delete_clip(self, clip_id: str, remove_file_from_disk: bool = True) -> bool:
        row = self._execute(
            f"SELECT is_file, file_path FROM {self.table} WHERE clip_id = ?;",
            (clip_id,),
        ).fetchone()
        if not row:
            return False

        file_path = row["file_path"]
        with self._lock:
            self._execute(
                f"DELETE FROM {self.table} WHERE clip_id = ?;",
                (clip_id,),
                commit=True,
            )
            self._execute(
                "DELETE FROM clip_fts WHERE clip_id = ?;",
                (clip_id,),
                commit=True,
            )
            if remove_file_from_disk and file_path:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        return True

    def delete_all(self, remove_files_from_disk: bool = True) -> int:
        """Delete this bucket and its FTS/file references, not other buckets."""
        with self._lock:
            file_paths = []
            if remove_files_from_disk:
                rows = self._execute(
                    f"SELECT file_path FROM {self.table} WHERE is_file = 1;"
                ).fetchall()
                file_paths = [row["file_path"] for row in rows if row["file_path"]]

            count = self._execute(
                f"SELECT COUNT(*) AS c FROM {self.table};"
            ).fetchone()["c"]
            self._execute(f"DELETE FROM {self.table};", commit=True)
            self._execute(
                """
                DELETE FROM clip_fts
                WHERE clip_id NOT IN (
                    SELECT clip_id FROM clipboard
                    UNION
                    SELECT clip_id FROM favourites
                );
                """,
                commit=True,
            )

            if remove_files_from_disk:
                for file_path in file_paths:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            return count

    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return self.list_clips(limit=limit)

        rows = []
        terms = [term.replace('"', '""') for term in query.split() if term]
        if terms:
            # Quoting prevents user punctuation from becoming FTS operators.
            fts_query = " AND ".join(f'"{term}"*' for term in terms)
            try:
                rows = self._execute(
                    f"""
                    SELECT c.clip_id, c.content_type, c.content_size,
                           c.preview_text, c.thumbnail, c.created_at,
                           c.source_app, c.file_name
                    FROM clip_fts
                    JOIN {self.table} AS c ON c.clip_id = clip_fts.clip_id
                    WHERE clip_fts MATCH ?
                    ORDER BY c.created_at ASC
                    LIMIT ?;
                    """,
                    (fts_query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                logger.warning("FTS query failed; using substring search", exc_info=True)

        if not rows:
            like_query = f"%{query}%"
            rows = self._execute(
                f"""
                SELECT clip_id, content_type, content_size, preview_text,
                       thumbnail, created_at, source_app, file_name
                FROM {self.table}
                WHERE full_text LIKE ? OR preview_text LIKE ?
                      OR file_name LIKE ? OR source_app LIKE ?
                      OR window_title LIKE ? OR tags LIKE ?
                ORDER BY created_at ASC
                LIMIT ?;
                """,
                (like_query,) * 6 + (limit,),
            ).fetchall()
        return self._rows_to_previews(rows)

    def move_row_to(self, dest_table: str, clip_id: str) -> bool:
        """Atomically move a row and its FTS entry to another clip bucket."""
        self._validate_table_name(dest_table)
        with self._lock:
            cursor = self.conn.cursor()
            try:
                cursor.execute("BEGIN;")
                cursor.execute(
                    f"SELECT * FROM {self.table} WHERE clip_id = ?;", (clip_id,)
                )
                row = cursor.fetchone()
                if not row:
                    cursor.execute("ROLLBACK;")
                    return False
                record = dict(row)

                cursor.execute(
                    f"DELETE FROM {self.table} WHERE clip_id = ?;", (clip_id,)
                )
                cursor.execute("DELETE FROM clip_fts WHERE clip_id = ?;", (clip_id,))

                columns = ", ".join(record.keys())
                placeholders = ", ".join("?" for _ in record)
                cursor.execute(
                    f"INSERT INTO {dest_table} ({columns}) VALUES ({placeholders});",
                    tuple(record.values()),
                )

                tags = " ".join(self.json_loads(record.get("tags")))
                content_text = " ".join(
                    filter(
                        None,
                        [
                            record.get("preview_text") or "",
                            record.get("full_text") or "",
                            record.get("file_name") or "",
                            tags,
                        ],
                    )
                )
                cursor.execute(
                    "INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);",
                    (clip_id, content_text),
                )
                cursor.execute("COMMIT;")
                return True
            except Exception:
                try:
                    cursor.execute("ROLLBACK;")
                except Exception:
                    pass
                raise

    def dedupe_within_bucket(self) -> int:
        """Remove duplicate hashes in this bucket and rebuild derived FTS rows."""
        with self._lock:
            cursor = self._execute(
                f"""
                DELETE FROM {self.table}
                WHERE clip_id NOT IN (
                    SELECT min(clip_id) FROM {self.table} GROUP BY content_hash
                );
                """,
                commit=True,
            )
            self.base.rebuild_clip_fts()
            return cursor.rowcount

    def purge_old(self, keep_last_n: int = 1000) -> int:
        """Retain only the newest requested number of clips in this bucket."""
        with self._lock:
            rows = self._execute(
                f"""
                SELECT clip_id FROM {self.table}
                ORDER BY created_at DESC LIMIT -1 OFFSET ?;
                """,
                (keep_last_n,),
            ).fetchall()
            removed = 0
            for row in rows:
                if self.delete_clip(row["clip_id"], remove_file_from_disk=True):
                    removed += 1
            return removed
