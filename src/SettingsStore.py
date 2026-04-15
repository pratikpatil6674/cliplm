import json
from pathlib import Path


class SettingsStore:
    def __init__(self, store_path, defaults=None):
        self.store_path = Path(store_path)
        self.defaults = defaults or {}
        self.settings = self._clone_defaults()
        self.load()

    def _clone_defaults(self):
        return json.loads(json.dumps(self.defaults))

    def load(self):
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.settings = self._clone_defaults()
            return self.settings

        try:
            self.settings = self._merge_dicts(
                self._clone_defaults(),
                json.loads(self.store_path.read_text(encoding="utf-8")),
            )
        except Exception:
            self.settings = self._clone_defaults()
        return self.settings

    def save(self, settings=None):
        if settings is not None:
            self.settings = self._merge_dicts(self._clone_defaults(), settings)

        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps(self.settings, indent=2),
            encoding="utf-8",
        )

    def get(self):
        return self.settings

    def update(self, updates):
        self.settings = self._merge_dicts(self.settings, updates)
        self.save()
        return self.settings

    def _merge_dicts(self, base, updates):
        merged = dict(base)
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged
