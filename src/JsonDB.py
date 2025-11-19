from __future__ import annotations
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


def _atomic_write(path: Path, data: Any) -> None:
    """Write JSON data atomically to path."""
    tmp_dir = path.parent
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(tmp_dir), delete=False) as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        tf.flush()
        os.fsync(tf.fileno())
        tmp_name = tf.name
    # atomic replace
    os.replace(tmp_name, str(path))


class BaseJsonDB:
    """Base JSON DB with atomic save and thread-safety."""

    def __init__(self, filepath: Path, default: Any):
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._default = default
        self._data = self._load()

    def _load(self) -> Any:
        if not self.filepath.exists():
            return self._default_copy()
        try:
            with self.filepath.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # If file corrupt, return default (do not raise)
            return self._default_copy()

    def _default_copy(self) -> Any:
        # Return a fresh copy of default. Handles dict/list defaults.
        if isinstance(self._default, dict):
            return dict(self._default)
        elif isinstance(self._default, list):
            return list(self._default)
        else:
            return self._default

    def _save(self) -> None:
        # atomic write of self._data
        _atomic_write(self.filepath, self._data)

    def reload(self) -> None:
        with self._lock:
            self._data = self._load()

    # --- convenience accessors ---
    def get_all_raw(self) -> Any:
        with self._lock:
            # return a shallow copy to avoid accidental external mutation
            if isinstance(self._data, dict):
                return dict(self._data)
            elif isinstance(self._data, list):
                return list(self._data)
            else:
                return self._data


class ClipboardDB(BaseJsonDB):
    """Store clipboard entries: { uuid: text }"""

    def __init__(self, filepath: Path):
        super().__init__(filepath, default={})

    def add(self, text: str, id: Optional[str] = None) -> str:
        """Add text, return generated id (or use provided id)."""
        with self._lock:
            if id is None:
                id = str(uuid.uuid4())
            self._data[id] = text
            self._save()
            return id

    def delete(self, id: str) -> bool:
        with self._lock:
            if id in self._data:
                del self._data[id]
                self._save()
                return True
            return False

    def delete_all(self):
        with self._lock:
            self._data = {}
            self._save()

    def get_item(self, id: str) -> Optional[str]:
        with self._lock:
            return self._data.get(id)

    def get_all(self) -> Dict[str, str]:
        return self.get_all_raw()


class FavoritesDB(BaseJsonDB):
    """Store favorites: { uuid: text }"""

    def __init__(self, filepath: Path):
        super().__init__(filepath, default={})

    def add(self, id: Optional[str] = None, text: str = "") -> str:
        with self._lock:
            if id is None:
                id = str(uuid.uuid4())
            self._data[id] = text
            self._save()
            return id

    def delete(self, id: str) -> bool:
        with self._lock:
            if id in self._data:
                del self._data[id]
                self._save()
                return True
            return False

    def get_item(self, id: str) -> Optional[str]:
        with self._lock:
            return self._data.get(id)

    def get_all(self) -> Dict[str, str]:
        return self.get_all_raw()


class ManualDB(BaseJsonDB):
    """
    Store manual entries: { uuid: [ title: str, text: str ] }
    Provides add/delete/get_all/edit operations.
    """

    def __init__(self, filepath: Path):
        super().__init__(filepath, default={})

    def add(self, title: str, text: str, id: Optional[str] = None) -> str:
        """Add a manual entry; return id."""
        with self._lock:
            if id is None:
                id = str(uuid.uuid4())
            self._data[id] = [title, text]
            self._save()
            return id

    def delete(self, id: str) -> bool:
        with self._lock:
            if id in self._data:
                del self._data[id]
                self._save()
                return True
            return False

    def edit(self, id: str, title: Optional[str] = None, text: Optional[str] = None) -> bool:
        """Edit title and/or text of the manual entry. Returns True if updated."""
        with self._lock:
            if id not in self._data:
                return False
            current = self._data[id]
            new_title = title if title is not None else current[0]
            new_text = text if text is not None else current[1]
            self._data[id] = [new_title, new_text]
            self._save()
            return True

    def get_item(self, id: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            v = self._data.get(id)
            if v is None:
                return None
            return (v[0], v[1])

    def get_all(self) -> Dict[str, List[str]]:
        return self.get_all_raw()
