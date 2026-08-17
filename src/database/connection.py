"""SQLite connection ownership, schema validation, and shared DB utilities."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from typing import Any, Optional, Tuple

from .schema import (
    CURRENT_SCHEMA_VERSION,
    FTS_SHADOW_TABLES,
    VERSION_ONE_SCHEMA,
    DatabaseCompatibilityError,
)


class BaseDB:
    """
    Own the shared SQLite connection and establish a safe database baseline.

    Construction does not blindly run CREATE TABLE statements. It first reads
    the version stored inside SQLite, verifies that the physical schema matches
    that version, and only then allows repositories to use the connection.
    """

    CLIP_SCHEMA_NAME = "clipboard"
    FAVS_SCHEMA_NAME = "favourites"
    NOTES_SCHEMA_NAME = "text_notes"

    def __init__(self, db_path: str, data_dir: str, journal_mode: str = "WAL"):
        self.db_path = os.path.abspath(db_path)
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.files_dir(), exist_ok=True)
        os.makedirs(self.thumbs_dir(), exist_ok=True)

        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        try:
            self._prepare_database(journal_mode)
        except Exception:
            self.conn.close()
            raise

    def _prepare_database(self, journal_mode: str) -> None:
        """Choose the safe startup path before repositories can access data."""
        schema_version = self._schema_version()

        # An older app cannot understand fields introduced by a newer app.
        if schema_version > CURRENT_SCHEMA_VERSION:
            raise DatabaseCompatibilityError(
                f"Database schema version {schema_version} is newer than the "
                f"supported version {CURRENT_SCHEMA_VERSION}. Install a newer "
                "ClipLM version to open this data."
            )

        # The version marker and the physical schema must agree.
        if schema_version == CURRENT_SCHEMA_VERSION:
            self._validate_version_one_schema()
            self._configure_pragmas(journal_mode)
            return

        # Version 0 is handled below. Other versions require a future migrator.
        if schema_version != 0:
            raise DatabaseCompatibilityError(
                f"Database schema version {schema_version} is not supported by "
                "this ClipLM version."
            )

        if self._has_schema_objects():
            # Pre-release databases contain version 1 objects but report 0.
            # Relabel them only after every schema object matches.
            self._validate_version_one_schema()
            self._configure_pragmas(journal_mode)
            with self.conn:
                self._set_schema_version(CURRENT_SCHEMA_VERSION)
            return

        # A genuinely empty database receives schema and marker together.
        self._configure_pragmas(journal_mode)
        with self.conn:
            self._init_schema()
            self._set_schema_version(CURRENT_SCHEMA_VERSION)
        self._validate_version_one_schema()

    def _schema_version(self) -> int:
        """Read ClipLM's integer format version stored in the SQLite header."""
        return int(self.conn.execute("PRAGMA user_version").fetchone()[0])

    def _set_schema_version(self, version: int) -> None:
        self.conn.execute(f"PRAGMA user_version = {version}")

    def _has_schema_objects(self) -> bool:
        """Distinguish a new database from an unversioned legacy database."""
        return self.conn.execute(
            """
            SELECT 1 FROM sqlite_schema
            WHERE name NOT LIKE 'sqlite_%'
            LIMIT 1
            """
        ).fetchone() is not None

    def _validate_version_one_schema(self) -> None:
        """Verify that tables and indexes match the version 1 contract."""
        rows = self.conn.execute(
            """
            SELECT type, name, sql FROM sqlite_schema
            WHERE name NOT LIKE 'sqlite_%'
            """
        ).fetchall()
        actual_objects = {(row["type"], row["name"]) for row in rows}
        expected_objects = {
            (object_type, name)
            for name, (object_type, _sql) in VERSION_ONE_SCHEMA.items()
        }
        expected_objects.update(
            ("table", table_name) for table_name in FTS_SHADOW_TABLES
        )
        if actual_objects != expected_objects:
            self._raise_schema_mismatch("database objects")

        actual_sql = {row["name"]: row["sql"] for row in rows}
        for name, (_object_type, expected_sql) in VERSION_ONE_SCHEMA.items():
            if self._normalize_schema_sql(actual_sql.get(name)) != (
                self._normalize_schema_sql(expected_sql)
            ):
                self._raise_schema_mismatch(name)

    @staticmethod
    def _normalize_schema_sql(sql: Optional[str]) -> str:
        # Formatting differences are irrelevant; SQL structure is not.
        return "".join((sql or "").casefold().split()).rstrip(";")

    @staticmethod
    def _raise_schema_mismatch(detail: str) -> None:
        raise DatabaseCompatibilityError(
            "The database is not the expected ClipLM schema version 1 "
            f"({detail} differs). It was left unchanged."
        )

    def _configure_pragmas(self, journal_mode: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA journal_mode = {journal_mode};")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA temp_store = MEMORY;")
        cursor.execute("PRAGMA foreign_keys = OFF;")
        self.conn.commit()

    def _init_schema(self) -> None:
        """Create version 1 only for a database already verified as empty."""
        with self._lock:
            cursor = self.conn.cursor()
            for _name, (_object_type, statement) in VERSION_ONE_SCHEMA.items():
                cursor.execute(statement)

    def files_dir(self) -> str:
        return os.path.join(self.data_dir, "files")

    def thumbs_dir(self) -> str:
        return os.path.join(self.data_dir, "thumbnails")

    def _path_for_new_file(self, ext: Optional[str] = None) -> str:
        folder = os.path.join(self.files_dir(), datetime.date.today().isoformat())
        os.makedirs(folder, exist_ok=True)
        filename = str(uuid.uuid4())
        if ext:
            filename = f"{filename}.{ext.lstrip('.')}"
        return os.path.join(folder, filename)

    def _thumb_path_for_new(self) -> str:
        folder = os.path.join(self.thumbs_dir(), datetime.date.today().isoformat())
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{uuid.uuid4()}.thumb")

    def _execute(self, sql: str, params: Tuple = (), commit: bool = False):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            if commit:
                self.conn.commit()
            return cursor

    def close(self) -> None:
        with self._lock:
            self.conn.commit()
            self.conn.close()

    @staticmethod
    def sha256(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def json_dumps(value: Any) -> str:
        return json.dumps(value or {})

    @staticmethod
    def json_loads(value: Optional[str]) -> Any:
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []

    def rebuild_clip_fts(self) -> None:
        """Rebuild derived full-text-search rows from both clip buckets."""
        with self._lock:
            self._execute("DELETE FROM clip_fts;", commit=True)
            for table_name in (self.CLIP_SCHEMA_NAME, self.FAVS_SCHEMA_NAME):
                rows = self._execute(
                    f"SELECT clip_id, preview_text, full_text, file_name, tags "
                    f"FROM {table_name};"
                ).fetchall()
                for row in rows:
                    tags = " ".join(self.json_loads(row["tags"]) or [])
                    content_text = " ".join(
                        filter(
                            None,
                            [
                                row["preview_text"] or "",
                                row["full_text"] or "",
                                row["file_name"] or "",
                                tags,
                            ],
                        )
                    )
                    self._execute(
                        "INSERT INTO clip_fts (clip_id, content_text) VALUES (?, ?);",
                        (row["clip_id"], content_text),
                    )
            self.conn.commit()
