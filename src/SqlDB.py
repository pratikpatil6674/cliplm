"""
- BaseDB: connection, PRAGMAS, schema creation for two identical buckets: 'clipboard' and 'favourites'.
- ClipboardTable: generic table wrapper operating on any table with the clipboard schema.
- NotesTable: text notes operations.
- ClipboardStore: facade exposing `clipboard` and `favourites` as separate ClipboardTable objects and convenience move methods.

Behavior:
- 'clipboard' and 'favourites' are independent tables with identical schema.
- Moving an item from one bucket to another is atomic (transactional), updates the FTS index,
  and preserves on-disk files (no deletion).
- Use a single shared sqlite connection across table objects.

Optional dependency: Pillow (for thumbnail generation). If not available thumbnail generation is skipped.
"""

from __future__ import annotations
import sqlite3
import os
import uuid
import hashlib
import json
import threading
import datetime
from typing import Optional, List, Dict, Any, Tuple

# Optional Pillow for thumbnails
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


def iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class BaseDB:
    """
    Shared DB connection, pragmas, schema creation for both clipboard-like tables and helpers.
    """

    CLIP_SCHEMA_NAME = "clipboard"      # canonical name
    FAVS_SCHEMA_NAME = "favourites"     # canonical name
    NOTES_SCHEMA_NAME = "text_notes"    # canonical name

    def __init__(self, db_path: str, data_dir: str, journal_mode: str = "WAL"):
        self.db_path = os.path.abspath(db_path)
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.files_dir(), exist_ok=True)
        os.makedirs(self.thumbs_dir(), exist_ok=True)

        self._lock = threading.RLock()
        # Single shared connection
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._configure_pragmas(journal_mode)
        self._init_schema()

    # ---------------- PRAGMAS ----------------
    def _configure_pragmas(self, journal_mode: str):
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA journal_mode = {journal_mode};")
        cur.execute("PRAGMA synchronous = NORMAL;")
        cur.execute("PRAGMA temp_store = MEMORY;")
        cur.execute("PRAGMA foreign_keys = OFF;")  # no FK between buckets by design
        self.conn.commit()

    # ---------------- Schema ----------------
    def _init_schema(self):
        """
        Create two identical tables (clipboard & favourites) and supporting structures (FTS5).
        """
        with self._lock:
            cur = self.conn.cursor()
            # Define a common clipboard-like schema. Both tables will use it.
            base_table_sql = """
            CREATE TABLE IF NOT EXISTS {table} (
                clip_id TEXT PRIMARY KEY,
                content_type TEXT,
                content_size INTEGER,
                content_hash TEXT,
                is_file INTEGER DEFAULT 0,
                file_path TEXT,
                file_name TEXT,
                thumbnail BLOB,
                preview_text TEXT,
                full_text TEXT,
                source_app TEXT,
                window_title TEXT,
                tags TEXT,
                language TEXT,
                metadata TEXT,
                created_at TEXT,
                modified_at TEXT
            );
            """
            cur.execute(base_table_sql.format(table=self.CLIP_SCHEMA_NAME))
            cur.execute(base_table_sql.format(table=self.FAVS_SCHEMA_NAME))

            notes_table_sql = """
            CREATE TABLE IF NOT EXISTS {table} (
                note_id TEXT PRIMARY KEY,
                content_type TEXT,
                title TEXT,
                main_text TEXT,
                preview_text TEXT,
                tags TEXT,
                created_at TEXT,
                modified_at TEXT
            );
            """
            cur.execute(notes_table_sql.format(table=self.NOTES_SCHEMA_NAME))

            # FTS5 table for searching across all buckets (clip_id unique across DB)
            cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clip_fts USING fts5(
                clip_id UNINDEXED,
                content_text,
                tokenize = 'porter'
            );
            """)
            # Indices for performance
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.CLIP_SCHEMA_NAME}_created ON {self.CLIP_SCHEMA_NAME}(created_at);")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.FAVS_SCHEMA_NAME}_created ON {self.FAVS_SCHEMA_NAME}(created_at);")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.CLIP_SCHEMA_NAME}_hash ON {self.CLIP_SCHEMA_NAME}(content_hash);")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.FAVS_SCHEMA_NAME}_hash ON {self.FAVS_SCHEMA_NAME}(content_hash);")
            # cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.NOTES_SCHEMA_NAME}_created ON {self.NOTES_SCHEMA_NAME}(created_at);")
            # cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.NOTES_SCHEMA_NAME}_hash ON {self.NOTES_SCHEMA_NAME}(content_hash);")
            self.conn.commit()

    # ---------------- File storage helpers ----------------
    def files_dir(self) -> str:
        return os.path.join(self.data_dir, "files")

    def thumbs_dir(self) -> str:
        return os.path.join(self.data_dir, "thumbnails")

    def _path_for_new_file(self, ext: Optional[str] = None) -> str:
        today = datetime.date.today().isoformat()
        folder = os.path.join(self.files_dir(), today)
        os.makedirs(folder, exist_ok=True)
        fname = str(uuid.uuid4())
        if ext:
            fname = f"{fname}.{ext.lstrip('.')}"
        return os.path.join(folder, fname)

    def _thumb_path_for_new(self) -> str:
        today = datetime.date.today().isoformat()
        folder = os.path.join(self.thumbs_dir(), today)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{uuid.uuid4()}.thumb")

    # ---------------- DB helpers ----------------
    def _execute(self, sql: str, params: Tuple = (), commit: bool = False):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            if commit:
                self.conn.commit()
            return cur

    def close(self):
        with self._lock:
            self.conn.commit()
            self.conn.close()

    # ---------------- Utilities ----------------
    @staticmethod
    def sha256(b: bytes) -> str:
        h = hashlib.sha256()
        h.update(b)
        return h.hexdigest()

    @staticmethod
    def json_dumps(x: Any) -> str:
        return json.dumps(x or {})

    @staticmethod
    def json_loads(s: Optional[str]) -> Any:
        if not s:
            return []
        try:
            return json.loads(s)
        except Exception:
            return []

    def generate_image_thumbnail(self, content_bytes: bytes, max_size: Tuple[int, int] = (256, 256)) -> Optional[bytes]:
        if not PIL_AVAILABLE:
            return None
        try:
            from io import BytesIO
            im = Image.open(BytesIO(content_bytes))
            im.thumbnail(max_size)
            out = BytesIO()
            im.save(out, format="JPEG", quality=75)
            return out.getvalue()
        except Exception:
            return None

    def rebuild_clip_fts(self):
        """
        Rebuild clip_fts from both tables.
        """
        with self._lock:
            self._execute("DELETE FROM clip_fts;", commit=True)
            cur = self._execute(f"SELECT clip_id, preview_text, full_text, file_name, tags FROM {self.CLIP_SCHEMA_NAME};")
            rows = cur.fetchall()
            for r in rows:
                tags = " ".join(self.json_loads(r["tags"]) or [])
                content_text = " ".join(filter(None, [r["preview_text"] or "", r["full_text"] or "", r["file_name"] or "", tags]))
                self._execute("INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);", (r["clip_id"], content_text))
            cur = self._execute(f"SELECT clip_id, preview_text, full_text, file_name, tags FROM {self.FAVS_SCHEMA_NAME};")
            rows = cur.fetchall()
            for r in rows:
                tags = " ".join(self.json_loads(r["tags"]) or [])
                content_text = " ".join(filter(None, [r["preview_text"] or "", r["full_text"] or "", r["file_name"] or "", tags]))
                self._execute("INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);", (r["clip_id"], content_text))
            self.conn.commit()


# ---------------- Generic ClipboardTable ----------------
class ClipboardTable:
    """
    Generic wrapper for a clipboard-like table. Use instances for 'clipboard' and 'favourites'.
    """

    FILE_ON_DISK_THRESHOLD = 256 * 1024  # 256 KB

    def __init__(self, base: BaseDB, table_name: str):
        self._validate_table_name(table_name)
        self.base = base
        self.table = table_name
        # reuse connection & helpers
        self.conn = base.conn
        self._lock = base._lock
        self._execute = base._execute
        self.sha256 = base.sha256
        self.json_dumps = base.json_dumps
        self.json_loads = base.json_loads
        self.generate_image_thumbnail = base.generate_image_thumbnail
        self._path_for_new_file = base._path_for_new_file
        self.rebuild_clip_fts = base.rebuild_clip_fts

    @staticmethod
    def _validate_table_name(name: str):
        # allow only alphanumerics and underscore to avoid SQL injection in f-strings
        if not name or not all(c.isalnum() or c == "_" for c in name):
            raise ValueError("Invalid table name")

    # ---------------- CRUD ----------------
    def add_clip(self,
                 content: bytes,
                 mime: str,
                 file_name: Optional[str] = None,
                 source_app: Optional[str] = None,
                 window_title: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 save_file_to_disk_if_large: bool = True,
                 preview_text: Optional[str] = None,
                 store_thumbnail: bool = True,
                 metadata: Optional[Dict[str, Any]] = None
                 ) -> str:
        """
        Insert new clip into this table. Deduplicate only within this table.
        Returns clip_id.
        """
        content_hash = self.sha256(content)
        now = iso_now()
        tags_json = self.json_dumps(tags or [])
        metadata_json = json.dumps(metadata or {})

        # Deduplicate within this bucket
        cur = self._execute(f"SELECT clip_id FROM {self.table} WHERE content_hash = ? LIMIT 1;", (content_hash,))
        row = cur.fetchone()
        if row:
            return row["clip_id"]

        clip_id = str(uuid.uuid4())
        size = len(content)

        is_file = 0
        file_path = None
        thumb_blob = None
        full_text = None

        if mime and (mime.startswith("text") or mime.endswith("xml") or mime.endswith("json")):
            try:
                full_text = content.decode("utf-8", errors="replace")
                if not preview_text:
                    preview_text = full_text[:500]  # First 500 chars as preview
                    if len(full_text) > 500:
                        preview_text += "..."
            except Exception:
                full_text = None
                preview_text = None

        if save_file_to_disk_if_large and size > self.FILE_ON_DISK_THRESHOLD:
            ext = None
            if file_name and '.' in file_name:
                ext = file_name.split('.')[-1]
            file_path = self._path_for_new_file(ext)
            with open(file_path, "wb") as f:
                f.write(content)
            is_file = 1
            if store_thumbnail and mime and mime.startswith("image"):
                thumb_blob = self.generate_image_thumbnail(content)
        else:
            if store_thumbnail and mime and mime.startswith("image"):
                thumb_blob = self.generate_image_thumbnail(content)

        # Insert row
        self._execute(f"""
            INSERT INTO {self.table} (
                clip_id, content_type, content_size, content_hash,
                is_file, file_path, file_name, thumbnail, preview_text,
                full_text, source_app, window_title, tags, language, metadata,
                created_at, modified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (clip_id, mime, size, content_hash, is_file, file_path, file_name, thumb_blob, preview_text,
              full_text, source_app, window_title, tags_json, None, metadata_json, now, now), commit=True)

        # Insert into FTS
        content_text = " ".join(filter(None, [preview_text or "", full_text or "", file_name or "", " ".join(tags or [])]))
        self._execute("INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);", (clip_id, content_text), commit=True)

        return clip_id

    def get_clip(self, clip_id: str, load_file: bool = False) -> Optional[Dict[str, Any]]:
        cur = self._execute(f"SELECT * FROM {self.table} WHERE clip_id = ?;", (clip_id,))
        r = cur.fetchone()
        if not r:
            return None
        d = dict(r)
        d["tags"] = self.json_loads(d.get("tags"))
        try:
            d["metadata"] = json.loads(d.get("metadata") or "{}")
        except Exception:
            d["metadata"] = {}
        if load_file and d.get("is_file"):
            try:
                with open(d.get("file_path"), "rb") as f:
                    d["content"] = f.read()
            except Exception:
                d["content"] = None
        return d

    def list_clips(self, limit: int = 100, offset: int = 0, order_by: str = "created_at DESC") -> List[Dict[str, Any]]:
        cur = self._execute(f"SELECT clip_id, content_type, content_size, preview_text, thumbnail, created_at, source_app, file_name FROM {self.table} ORDER BY {order_by} LIMIT ? OFFSET ?;", (limit, offset))
        return [dict(r) for r in cur.fetchall()]

    def delete_clip(self, clip_id: str, remove_file_from_disk: bool = True) -> bool:
        row = self._execute(f"SELECT is_file, file_path FROM {self.table} WHERE clip_id = ?;", (clip_id,)).fetchone()
        if not row:
            return False
        file_path = row["file_path"]
        with self._lock:
            # Delete from table and FTS
            self._execute(f"DELETE FROM {self.table} WHERE clip_id = ?;", (clip_id,), commit=True)
            self._execute("DELETE FROM clip_fts WHERE clip_id = ?;", (clip_id,), commit=True)
            if remove_file_from_disk and file_path:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        return True

    def delete_all(self, remove_files_from_disk: bool = True) -> int:
        """
        Delete all rows from this clipboard bucket.
        Does NOT touch other buckets.
        Removes thumbnails and file_path targets from disk if requested.
        Cleans FTS entries for this table.

        Returns number of rows deleted.
        """
        with self._lock:
            # Collect file paths first (only if we need to remove files)
            file_paths = []
            if remove_files_from_disk:
                cur = self._execute(f"SELECT file_path FROM {self.table} WHERE is_file = 1;")
                for r in cur.fetchall():
                    if r["file_path"]:
                        file_paths.append(r["file_path"])

            # Count rows
            cur = self._execute(f"SELECT COUNT(*) AS c FROM {self.table};")
            count = cur.fetchone()["c"]

            # Delete rows from this bucket
            self._execute(f"DELETE FROM {self.table};", commit=True)

            # Remove corresponding FTS entries
            # FTS contains clip_id across both buckets, so we must remove only those belonging to this table.
            self._execute("""
                DELETE FROM clip_fts
                WHERE clip_id NOT IN (
                    SELECT clip_id FROM clipboard
                    UNION
                    SELECT clip_id FROM favourites
                );
            """, commit=True)

            # Remove files from disk
            if remove_files_from_disk:
                for fp in file_paths:
                    try:
                        os.remove(fp)
                    except Exception:
                        pass

            return count

    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        # Search via FTS for clip_id match then filter by presence in this table
        cur = self._execute("SELECT f.clip_id FROM clip_fts f WHERE clip_fts MATCH ? LIMIT ?;", (query, limit))
        ids = [r["clip_id"] for r in cur.fetchall()]
        if not ids:
            # fallback LIKE in this table
            q = f"%{query}%"
            cur = self._execute(f"SELECT * FROM {self.table} WHERE preview_text LIKE ? OR file_name LIKE ? ORDER BY created_at DESC LIMIT ?;", (q, q, limit))
            return [dict(r) for r in cur.fetchall()]
        # Fetch only those ids that exist in this table (keeps buckets independent)
        placeholders = ",".join("?" for _ in ids)
        cur = self._execute(f"SELECT * FROM {self.table} WHERE clip_id IN ({placeholders}) ORDER BY created_at DESC LIMIT ?;", tuple(ids) + (limit,))
        return [dict(r) for r in cur.fetchall()]

    # ---------------- Move row ----------------
    def move_row_to(self, dest_table: str, clip_id: str) -> bool:
        """
        Atomically move a row from self.table to dest_table.
        Both tables must have identical schema.
        Returns True if moved, False if source row not found.
        """
        self._validate_table_name(dest_table)
        src = self.table
        dest = dest_table

        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("BEGIN;")
                # 1) Fetch row from source
                cur.execute(f"SELECT * FROM {src} WHERE clip_id = ?;", (clip_id,))
                row = cur.fetchone()
                if not row:
                    cur.execute("ROLLBACK;")
                    return False
                row_dict = dict(row)

                # 2) Delete from source
                cur.execute(f"DELETE FROM {src} WHERE clip_id = ?;", (clip_id,))

                # 3) Delete any existing FTS entry for this clip_id (to avoid duplicates)
                cur.execute("DELETE FROM clip_fts WHERE clip_id = ?;", (clip_id,))

                # 4) Insert into destination
                columns = ", ".join(row_dict.keys())
                placeholders = ", ".join("?" for _ in row_dict)
                values = tuple(row_dict.values())
                cur.execute(f"INSERT INTO {dest} ({columns}) VALUES ({placeholders});", values)

                # 5) Insert into FTS for destination (content_text built from preview/full/file/tags)
                tags = " ".join(self.json_loads(row_dict.get("tags")))
                content_text = " ".join(filter(None, [row_dict.get("preview_text") or "", row_dict.get("full_text") or "", row_dict.get("file_name") or "", tags]))
                cur.execute("INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);", (clip_id, content_text))

                cur.execute("COMMIT;")
                return True
            except Exception:
                try:
                    cur.execute("ROLLBACK;")
                except Exception:
                    pass
                raise

    # ---------------- Utilities ----------------
    def dedupe_within_bucket(self) -> int:
        """
        Remove duplicate rows within this table based on content_hash, keeping the earliest clip_id.
        Returns number removed.
        """
        with self._lock:
            cur = self._execute(f"""
                DELETE FROM {self.table}
                WHERE clip_id NOT IN (
                    SELECT min(clip_id) FROM {self.table} GROUP BY content_hash
                );
            """, commit=True)
            removed = cur.rowcount
            self.base.rebuild_clip_fts()
            return removed

    def purge_old(self, keep_last_n: int = 1000) -> int:
        """
        Keep only the most recent keep_last_n items in this table.
        Returns number removed.
        """
        with self._lock:
            cur = self._execute(f"SELECT clip_id FROM {self.table} ORDER BY created_at DESC LIMIT -1 OFFSET ?;", (keep_last_n,))
            to_delete = [r["clip_id"] for r in cur.fetchall()]
            removed = 0
            for cid in to_delete:
                if self.delete_clip(cid, remove_file_from_disk=True):
                    removed += 1
            return removed


# ---------------- NotesTable ----------------
class NotesTable:
    """
    CRUD and simple search for text_notes table.
    """

    def __init__(self, base: BaseDB):
        self.base = base
        self._execute = base._execute
        self.json_dumps = base.json_dumps
        self.json_loads = base.json_loads
        self._lock = base._lock

    def add_note(self, title: str, main_text: str, tags: Optional[List[str]] = None) -> str:
        note_id = str(uuid.uuid4())
        now = iso_now()
        preview = (main_text[:512] + "...") if len(main_text) > 512 else main_text
        tags_json = self.json_dumps(tags or [])
        self._execute("INSERT INTO text_notes (note_id, content_type, title, main_text, preview_text, tags, created_at, modified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                      (note_id, 'text', title, main_text, preview, tags_json, now, now), commit=True)
        return note_id

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        r = self._execute("SELECT * FROM text_notes WHERE note_id = ?;", (note_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["tags"] = self.json_loads(d.get("tags"))
        return d

    def update_note(self, note_id: str, title: Optional[str] = None, main_text: Optional[str] = None, tags: Optional[List[str]] = None) -> bool:
        r = self.get_note(note_id)
        if not r:
            return False
        title = title if title is not None else r["title"]
        main_text = main_text if main_text is not None else r["main_text"]
        preview = (main_text[:512] + "...") if len(main_text) > 512 else main_text
        tags_json = self.json_dumps(tags if tags is not None else r.get("tags", []))
        now = iso_now()
        self._execute("UPDATE text_notes SET title = ?, main_text = ?, preview_text = ?, tags = ?, modified_at = ? WHERE note_id = ?;",
                      (title, main_text, preview, tags_json, now, note_id), commit=True)
        return self.get_note(note_id)

    def delete_note(self, note_id: str) -> bool:
        cur = self._execute("DELETE FROM text_notes WHERE note_id = ?;", (note_id,), commit=True)
        return cur.rowcount > 0

    def list_notes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        cur = self._execute("SELECT note_id, content_type, title, preview_text, created_at, modified_at FROM text_notes ORDER BY modified_at DESC LIMIT ? OFFSET ?;", (limit, offset))
        return [dict(r) for r in cur.fetchall()]

    def search_notes(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        cur = self._execute("SELECT * FROM text_notes WHERE title LIKE ? OR main_text LIKE ? OR preview_text LIKE ? LIMIT ?;", (q, q, q, limit))
        return [dict(r) for r in cur.fetchall()]


# ---------------- Facade ----------------
class ClipboardStore:
    """
    Facade exposing:
      - store.clipboard (ClipboardTable on 'clipboard')
      - store.favourites (ClipboardTable on 'favourites')
      - store.notes (NotesTable)
      - convenience move methods: move_to_favourites / move_to_clipboard
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

    def close(self):
        self.base.close()


# ---------------- Usage example (for reference) ----------------
if __name__ == "__main__":
    # quick demo (not a unit test)
    store = ClipboardStore("clip_demo.db", "clip_demo_store")

    # add an item to clipboard
    cid = store.clipboard.add_clip(b"Hello world", mime="text/plain", preview_text="Hello world", source_app="Demo")
    print("added to clipboard:", cid)

    # move to favourites
    moved = store.move_to_favourites(cid)
    print("moved to favourites:", moved)

    # attempt to get from clipboard (should be None)
    print("from clipboard:", store.clipboard.get_clip(cid))

    # get from favourites
    print("from favourites:", store.favourites.get_clip(cid))

    # cleanup
    store.close()
