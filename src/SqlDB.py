"""
sqlite database implementation:
- BaseDB: connection, pragmas, file storage helpers, common utilities.
- ClipboardTable: operations for clipboard table (add/get/list/delete/search/dedupe).
- FavouritesTable: operations for favourites table.
- NotesTable: operations for text_notes table.
- ClipboardStore: facade composing the three tables.

Optional dependency: Pillow for thumbnail generation.
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

# Optional Pillow
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

def iso_now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class BaseDB:
    """
    Common DB connection, PRAGMA setup, file storage helpers, and utilities.
    """

    def __init__(self, db_path: str, data_dir: str, journal_mode: str = "WAL"):
        self.db_path = os.path.abspath(db_path)
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.files_dir(), exist_ok=True)
        os.makedirs(self.thumbs_dir(), exist_ok=True)

        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # self._configure_pragmas(journal_mode)
        self._init_schema()

    # ----------------- PRAGMA and schema -----------------
    def _configure_pragmas(self, journal_mode: str):
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode = ?;", (journal_mode,))
        cur.execute("PRAGMA synchronous = NORMAL;")
        cur.execute("PRAGMA temp_store = MEMORY;")
        cur.execute("PRAGMA foreign_keys = ON;")
        self.conn.commit()

    def _init_schema(self):
        """
        Create tables used by subclasses. Subclasses may extend schema further if required.
        """
        with self._lock:
            cur = self.conn.cursor()
            # clipboard table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS clipboard (
                clip_id TEXT PRIMARY KEY,
                content_type TEXT,
                content_size INTEGER,
                content_hash TEXT UNIQUE,
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
            );""")
            # favourites
            cur.execute("""
            CREATE TABLE IF NOT EXISTS favourites (
                fav_id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT NOT NULL,
                added_at TEXT,
                note TEXT,
                FOREIGN KEY(clip_id) REFERENCES clipboard(clip_id) ON DELETE CASCADE
            );""")
            # text notes
            cur.execute("""
            CREATE TABLE IF NOT EXISTS text_notes (
                note_id TEXT PRIMARY KEY,
                title TEXT,
                main_text TEXT,
                preview_text TEXT,
                tags TEXT,
                created_at TEXT,
                modified_at TEXT
            );""")
            # FTS5 virtual table for searching clip content. Keep separate table for performance.
            cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clip_fts USING fts5(
                clip_id UNINDEXED,
                content_text,
                tokenize = 'porter'
            );""")
            # index hints
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clip_created ON clipboard(created_at);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_clip_hash ON clipboard(content_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fav_clip ON favourites(clip_id);")
            self.conn.commit()

    # ----------------- File storage helpers -----------------
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

    # ----------------- DB helpers -----------------
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

    # ----------------- Utilities -----------------
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
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}

    # Thumbnail generation (optional)
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

    # Rebuild FTS (subclasses may call)
    def rebuild_clip_fts(self):
        with self._lock:
            self._execute("DELETE FROM clip_fts;", commit=True)
            cur = self._execute("SELECT clip_id, preview_text, full_text, file_name, tags FROM clipboard;")
            rows = cur.fetchall()
            for r in rows:
                tags = " ".join(self.json_loads(r["tags"]) or [])
                content_text = " ".join(filter(None, [r["preview_text"] or "", r["full_text"] or "", r["file_name"] or "", tags]))
                self._execute("INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);", (r["clip_id"], content_text))
            self.conn.commit()


# ----------------- ClipboardTable -----------------
class ClipboardTable(BaseDB):
    """
    Clipboard-specific operations: add_clip, get_clip, list_clips, delete_clip, search, dedupe, purge_old.
    """

    FILE_ON_DISK_THRESHOLD = 256 * 1024  # store >256KB to disk by default

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
        Add a clipboard item. Returns clip_id. Deduplicates by SHA-256 content hash.
        """
        content_hash = self.sha256(content)
        now = iso_now()
        tags_json = self.json_dumps(tags or [])
        metadata_json = self.json_dumps(metadata or {})

        # Deduplicate
        cur = self._execute("SELECT clip_id FROM clipboard WHERE content_hash = ? LIMIT 1;", (content_hash,))
        row = cur.fetchone()
        if row:
            return row["clip_id"]

        clip_id = str(uuid.uuid4())
        size = len(content)

        is_file = 0
        file_path = None
        thumb_blob = None
        full_text = None

        # quick heuristic for text extraction
        if mime and (mime.startswith("text") or mime.endswith("xml") or mime.endswith("json")):
            try:
                full_text = content.decode("utf-8", errors="replace")
            except Exception:
                full_text = None

        if save_file_to_disk_if_large and size > self.FILE_ON_DISK_THRESHOLD:
            ext = None
            if file_name and '.' in file_name:
                ext = file_name.split('.')[-1]
            file_path = self._path_for_new_file(ext)
            with open(file_path, "wb") as f:
                f.write(content)
            is_file = 1

            # generate thumbnail if image
            if store_thumbnail and mime and mime.startswith("image"):
                thumb_blob = self.generate_image_thumbnail(content)

        else:
            # small content - do not persist content bytes in table by default (keeps DB small).
            # but create thumbnail if image
            if store_thumbnail and mime and mime.startswith("image"):
                thumb_blob = self.generate_image_thumbnail(content)

        # Insert row
        self._execute("""
            INSERT INTO clipboard (
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
        cur = self._execute("SELECT * FROM clipboard WHERE clip_id = ?;", (clip_id,))
        r = cur.fetchone()
        if not r:
            return None
        d = dict(r)
        d["tags"] = self.json_loads(d.get("tags"))
        d["metadata"] = self.json_loads(d.get("metadata"))
        if load_file and d.get("is_file"):
            try:
                with open(d.get("file_path"), "rb") as f:
                    d["content"] = f.read()
            except Exception:
                d["content"] = None
        return d

    def list_clips(self, limit: int = 100, offset: int = 0, order_by: str = "created_at DESC") -> List[Dict[str, Any]]:
        cur = self._execute(f"SELECT clip_id, content_type, content_size, preview_text, created_at, source_app, file_name FROM clipboard ORDER BY {order_by} LIMIT ? OFFSET ?;", (limit, offset))
        return [dict(r) for r in cur.fetchall()]

    def delete_clip(self, clip_id: str, remove_file_from_disk: bool = True) -> bool:
        row = self._execute("SELECT is_file, file_path FROM clipboard WHERE clip_id = ?;", (clip_id,)).fetchone()
        if not row:
            return False
        file_path = row["file_path"]
        self._execute("DELETE FROM clipboard WHERE clip_id = ?;", (clip_id,), commit=True)
        self._execute("DELETE FROM clip_fts WHERE clip_id = ?;", (clip_id,), commit=True)
        if remove_file_from_disk and file_path:
            try:
                os.remove(file_path)
            except Exception:
                pass
        return True

    def search(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        # Use FTS5; if no results, fallback to LIKE.
        cur = self._execute("SELECT c.* FROM clip_fts f JOIN clipboard c ON c.clip_id = f.clip_id WHERE clip_fts MATCH ? ORDER BY c.created_at DESC LIMIT ?;", (query, limit))
        rows = cur.fetchall()
        if rows:
            return [dict(r) for r in rows]
        q = f"%{query}%"
        cur = self._execute("SELECT * FROM clipboard WHERE preview_text LIKE ? OR file_name LIKE ? ORDER BY created_at DESC LIMIT ?;", (q, q, limit))
        return [dict(r) for r in cur.fetchall()]

    def dedupe_keep_first(self) -> int:
        """
        Remove duplicate clipboard rows keeping the earliest clip_id per content_hash.
        Returns number removed.
        """
        cur = self._execute("""
            DELETE FROM clipboard
            WHERE clip_id NOT IN (
                SELECT min(clip_id) FROM clipboard GROUP BY content_hash
            );
        """, commit=True)
        removed = cur.rowcount
        self.rebuild_clip_fts()
        return removed

    def purge_old(self, keep_last_n: int = 1000) -> int:
        cur = self._execute("SELECT clip_id FROM clipboard ORDER BY created_at DESC LIMIT -1 OFFSET ?;", (keep_last_n,))
        to_delete = [r["clip_id"] for r in cur.fetchall()]
        removed = 0
        for cid in to_delete:
            if self.delete_clip(cid, remove_file_from_disk=True):
                removed += 1
        return removed


# ----------------- FavouritesTable -----------------
class FavouritesTable(BaseDB):
    """
    Manages favourites table. Assumes clipboard table exists and has clip_id primary key.
    """

    def add_favourite(self, clip_id: str, note: Optional[str] = None) -> int:
        now = iso_now()
        cur = self._execute("INSERT INTO favourites (clip_id, added_at, note) VALUES (?, ?, ?);", (clip_id, now, note), commit=True)
        return cur.lastrowid

    def remove_favourite_by_id(self, fav_id: int) -> bool:
        cur = self._execute("DELETE FROM favourites WHERE fav_id = ?;", (fav_id,), commit=True)
        return cur.rowcount > 0

    def remove_favourite_by_clip(self, clip_id: str) -> int:
        cur = self._execute("DELETE FROM favourites WHERE clip_id = ?;", (clip_id,), commit=True)
        return cur.rowcount

    def list_favourites(self, limit: int = 100) -> List[Dict[str, Any]]:
        cur = self._execute("SELECT f.fav_id, f.clip_id, f.added_at, f.note, c.preview_text, c.file_name FROM favourites f LEFT JOIN clipboard c ON c.clip_id = f.clip_id ORDER BY f.added_at DESC LIMIT ?;", (limit,))
        return [dict(r) for r in cur.fetchall()]


# ----------------- NotesTable -----------------
class NotesTable(BaseDB):
    """
    Text notes storage: CRUD and simple search.
    """

    def add_note(self, title: str, main_text: str, tags: Optional[List[str]] = None) -> str:
        note_id = str(uuid.uuid4())
        now = iso_now()
        preview = (main_text[:512] + "...") if len(main_text) > 512 else main_text
        tags_json = self.json_dumps(tags or [])
        self._execute("INSERT INTO text_notes (note_id, title, main_text, preview_text, tags, created_at, modified_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                      (note_id, title, main_text, preview, tags_json, now, now), commit=True)
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
        return True

    def delete_note(self, note_id: str) -> bool:
        cur = self._execute("DELETE FROM text_notes WHERE note_id = ?;", (note_id,), commit=True)
        return cur.rowcount > 0

    def list_notes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        cur = self._execute("SELECT note_id, title, preview_text, created_at, modified_at FROM text_notes ORDER BY modified_at DESC LIMIT ? OFFSET ?;", (limit, offset))
        return [dict(r) for r in cur.fetchall()]

    def search_notes(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        cur = self._execute("SELECT * FROM text_notes WHERE title LIKE ? OR main_text LIKE ? OR preview_text LIKE ? LIMIT ?;", (q, q, q, limit))
        return [dict(r) for r in cur.fetchall()]


# ----------------- Facade: ClipboardStore -----------------
class ClipboardStore:
    """
    Facade that composes ClipboardTable, FavouritesTable, and NotesTable.
    They all share the same sqlite connection and file dirs by design.
    """

    def __init__(self, db_path: str, data_dir: str):
        # Create a single BaseDB instance and share its connection by passing paths to subclasses.
        # Subclasses instantiate their own BaseDB, which will create a connection to the same file.
        # For thread-safety and simplicity, user may prefer a single shared BaseDB instance.
        # Here, to keep classes independent, we create one primary BaseDB and then monkeypatch connections.
        self.base = BaseDB(db_path, data_dir)
        # create table wrappers that reuse the same sqlite connection & lock
        self.clipboard = ClipboardTable.__new__(ClipboardTable)
        self.favourites = FavouritesTable.__new__(FavouritesTable)
        self.notes = NotesTable.__new__(NotesTable)

        # shallow-copy base attributes into wrappers so they share the same connection and helpers
        for obj in (self.clipboard, self.favourites, self.notes):
            # copy relevant attributes from base
            obj.db_path = self.base.db_path
            obj.data_dir = self.base.data_dir
            obj._lock = self.base._lock
            obj.conn = self.base.conn
            obj.json_dumps = self.base.json_dumps
            obj.json_loads = self.base.json_loads
            obj.sha256 = self.base.sha256
            obj.generate_image_thumbnail = self.base.generate_image_thumbnail
            obj.files_dir = self.base.files_dir
            obj.thumbs_dir = self.base.thumbs_dir
            obj._path_for_new_file = self.base._path_for_new_file
            obj._thumb_path_for_new = self.base._thumb_path_for_new
            # bind execute and rebuild function
            obj._execute = self.base._execute
            obj.rebuild_clip_fts = self.base.rebuild_clip_fts

        # also keep reference for closing
        self._closed = False

    def close(self):
        if not self._closed:
            self.base.close()
            self._closed = True

if __name__ == "__main__":
    store = ClipboardStore("./clip.db", "./clipstore")

    # add a text clip
    clip_id = store.clipboard.add_clip(b"hello world", mime="text/plain", preview_text="hello world", source_app="Terminal")
    print(store.clipboard.get_clip(clip_id))

    # add favourite
    fav_id = store.favourites.add_favourite(clip_id, note="useful snippet")

    # add note
    note_id = store.notes.add_note("Meeting notes", "Discussed X, Y, Z", tags=["meeting"])

    # search clips
    results = store.clipboard.search("hello")

    store.close()