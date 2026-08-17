"""Versioned SQLite schema contracts and compatibility errors."""

# SQLite initializes PRAGMA user_version to 0. ClipLM writes this value into
# the database file so future releases know which migrations are required.
CURRENT_SCHEMA_VERSION = 1


class DatabaseCompatibilityError(RuntimeError):
    """Raised before writes when a database is not compatible with this build."""


# This is the permanent definition of the first public database format. Keep it
# unchanged after version 1 ships. A future schema belongs in a new versioned
# definition and must be reached through a migration.
VERSION_ONE_SCHEMA = {
    "clipboard": (
        "table",
        """
        CREATE TABLE clipboard (
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
        )
        """,
    ),
    "favourites": (
        "table",
        """
        CREATE TABLE favourites (
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
        )
        """,
    ),
    "text_notes": (
        "table",
        """
        CREATE TABLE text_notes (
            note_id TEXT PRIMARY KEY,
            content_type TEXT,
            title TEXT,
            main_text TEXT,
            preview_text TEXT,
            tags TEXT,
            created_at TEXT,
            modified_at TEXT
        )
        """,
    ),
    "clip_fts": (
        "table",
        """
        CREATE VIRTUAL TABLE clip_fts USING fts5(
            clip_id UNINDEXED,
            content_text,
            tokenize = 'porter'
        )
        """,
    ),
    "idx_clipboard_created": (
        "index",
        "CREATE INDEX idx_clipboard_created ON clipboard(created_at)",
    ),
    "idx_favourites_created": (
        "index",
        "CREATE INDEX idx_favourites_created ON favourites(created_at)",
    ),
    "idx_clipboard_hash": (
        "index",
        "CREATE INDEX idx_clipboard_hash ON clipboard(content_hash)",
    ),
    "idx_favourites_hash": (
        "index",
        "CREATE INDEX idx_favourites_hash ON favourites(content_hash)",
    ),
}

# FTS5 creates these internal tables automatically when clip_fts is created.
# They are included during validation so a partial FTS setup is not accepted.
FTS_SHADOW_TABLES = {
    "clip_fts_config",
    "clip_fts_content",
    "clip_fts_data",
    "clip_fts_docsize",
    "clip_fts_idx",
}
