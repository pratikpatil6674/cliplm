"""
Backward-compatible database imports.

The implementation now lives in the database package. Keep this facade while
older modules or integrations may still import SqlDB; new code should import
the stable API directly from database.
"""

from database import (
    CURRENT_SCHEMA_VERSION,
    FTS_SHADOW_TABLES,
    VERSION_ONE_SCHEMA,
    BaseDB,
    ClipboardStore,
    ClipboardTable,
    DatabaseCompatibilityError,
    DatabaseRecord,
    NotesTable,
    iso_now,
)


__all__ = [
    "BaseDB",
    "ClipboardStore",
    "ClipboardTable",
    "CURRENT_SCHEMA_VERSION",
    "DatabaseCompatibilityError",
    "DatabaseRecord",
    "FTS_SHADOW_TABLES",
    "NotesTable",
    "VERSION_ONE_SCHEMA",
    "iso_now",
]
