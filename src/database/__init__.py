"""Stable public database API, independent of the internal module layout."""

from .clipboard_repository import ClipboardTable
from .connection import BaseDB
from .notes_repository import NotesTable
from .records import DatabaseRecord
from .schema import (
    CURRENT_SCHEMA_VERSION,
    FTS_SHADOW_TABLES,
    VERSION_ONE_SCHEMA,
    DatabaseCompatibilityError,
)
from .store import ClipboardStore
from .utils import iso_now


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
