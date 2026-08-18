"""Construction helpers for non-visual application services.

This factory owns constructor ordering and shared dependencies. It deliberately
does not connect widgets or presenters; visual composition remains in
``tab_composer`` so service creation can evolve independently from the UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from database import ClipboardStore
from services.ai_service import LLMService
from services.clipboard_service import ClipboardService
from services.translate_service import TranslateService
from storage.llm_profiles import active_profile
from storage.prompts_store import PromptsStore


@dataclass
class ApplicationServices:
    """Runtime services created once by the application composition root."""

    clipboard: ClipboardService
    ai: LLMService
    translate: TranslateService
    clips: ClipboardStore
    prompts: PromptsStore


def build_application_services(
    window,
    config_dir: str | Path,
    data_dir: str | Path,
    settings: dict[str, Any],
) -> ApplicationServices:
    """Create services and stores with their required shared dependencies.

    AI and LLM translation share one LLMService. Selecting another profile can
    therefore reconfigure one long-lived object without rebuilding either tab.
    """
    profile = active_profile(settings.get("ai", {})) or {}
    ai_service = LLMService(
        endpoint=profile.get("endpoint", ""),
        api_key=profile.get("api_key", ""),
        model=profile.get("model", ""),
        profile_name=profile.get("name", ""),
    )
    translate_service = TranslateService(ai_service)
    translate_service.configure(
        provider=settings.get("translate", {}).get("api", "google"),
        llm_service=ai_service,
    )

    # ClipboardService receives the window for desktop show/hide behavior;
    # persistence remains isolated behind ClipboardStore repositories.
    return ApplicationServices(
        clipboard=ClipboardService(window),
        ai=ai_service,
        translate=translate_service,
        clips=ClipboardStore(Path(data_dir) / "clipboard.db", str(data_dir)),
        prompts=PromptsStore(Path(config_dir) / "prompts.toml"),
    )
