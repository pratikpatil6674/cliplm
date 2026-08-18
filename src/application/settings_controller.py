"""Settings persistence and runtime reconfiguration.

This is the boundary between JSON-shaped user configuration and live Qt/service
objects. Views collect values, SettingsStore persists them, and this controller
applies the resulting state without reconstructing the application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QApplication

from storage.default_settings import DEFAULT_SETTINGS
from storage.llm_profiles import active_profile, normalize_ai_settings
from storage.settings_store import SettingsStore
from ui.theme.manager import apply_app_theme


class SettingsController:
    """Own settings persistence and apply settings to runtime collaborators.

    App reads settings through a property because SettingsStore replaces the
    mapping after updates; callers therefore never receive an obsolete snapshot.
    """

    def __init__(self, data_dir: str | Path):
        self.store = SettingsStore(
            Path(data_dir) / "settings.json",
            defaults=DEFAULT_SETTINGS,
        )
        self.settings = self.store.get()
        self._normalize_ai_settings()

    def _normalize_ai_settings(self) -> None:
        # Normalize legacy settings once at the storage boundary so every
        # feature can rely on the current profile-based schema.
        normalized = normalize_ai_settings(self.settings.get("ai", {}))
        if normalized != self.settings.get("ai", {}):
            self.settings["ai"] = normalized
            self.store.save(self.settings)

    def update(self, updates: dict[str, Any]) -> dict[str, Any]:
        self.settings = self.store.update(updates)
        return self.settings

    def save_from_views(self, settings_tab, translate_tab) -> dict[str, Any]:
        # Selectors and general controls live in separate tabs, but they form
        # one persisted translation configuration.
        updated = settings_tab.get_settings()
        updated["translate"]["source_language"] = (
            translate_tab.get_source_language()
        )
        updated["translate"]["destination_language"] = (
            translate_tab.get_destination_language()
        )
        self.settings = self.store.update(updated)
        settings_tab.set_settings(self.settings)
        return self.settings

    def save_translate_languages(
        self,
        source_language: str,
        destination_language: str,
    ) -> dict[str, Any]:
        return self.update(
            {
                "translate": {
                    "source_language": source_language,
                    "destination_language": destination_language,
                }
            }
        )

    def apply_appearance(self, tabs=None) -> None:
        appearance = self.settings.get("appearance", {})
        app = QApplication.instance()
        if app is None:
            return

        apply_app_theme(
            app,
            theme_name=appearance.get("theme", "blue"),
            dark_mode=appearance.get("dark_mode", False),
        )
        if tabs is not None:
            tabs.set_dark_mode(appearance.get("dark_mode", False))

    def configure_ai(self, ai_service, ai_presenter=None) -> None:
        # Reconfigure the existing QObject because presenter signals are wired
        # to this instance for the lifetime of the application.
        profile = active_profile(self.settings.get("ai", {})) or {}
        ai_service.configure(
            endpoint=profile.get("endpoint", ""),
            api_key=profile.get("api_key", ""),
            model=profile.get("model", ""),
            profile_name=profile.get("name", ""),
        )
        if ai_presenter is not None:
            ai_presenter.show_model_identity()

    def configure_translation(self, translate_service, translate_tab=None) -> None:
        provider = self.settings.get("translate", {}).get("api", "google")
        translate_service.configure(
            provider=provider,
            llm_service=translate_service.llm_service,
        )
        if translate_tab is not None:
            translate_tab.set_translation_provider(provider)

    def apply_translate_visibility(
        self,
        tabs,
        translate_tab,
        clipboard_tab,
    ) -> None:
        enabled = self.settings.get("translate", {}).get("enabled", True)
        translate_index = tabs.indexOf(translate_tab)
        if translate_index < 0:
            return

        tabs.setTabVisible(translate_index, enabled)
        if not enabled and tabs.currentWidget() is translate_tab:
            tabs.setCurrentWidget(clipboard_tab)
