from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse
from uuid import uuid4


class LLMProfileValidationError(ValueError):
    """Raised when a profile cannot be saved safely."""


def new_profile_id() -> str:
    return uuid4().hex


def normalize_ai_settings(ai_settings: Mapping[str, Any] | None) -> dict:
    """Return the current profile schema, migrating legacy single-model settings."""
    source = dict(ai_settings or {})
    raw_profiles = source.get("profiles")

    if isinstance(raw_profiles, list) and raw_profiles:
        profiles = _normalize_profiles(raw_profiles)
    elif _has_legacy_profile(source):
        profiles = [
            {
                "id": new_profile_id(),
                "name": "Default",
                "endpoint": str(source.get("endpoint", "")).strip(),
                "model": str(source.get("model", "")).strip(),
                "api_key": str(source.get("api_key", "")).strip(),
            }
        ]
    else:
        profiles = []

    active_profile_id = str(source.get("active_profile_id", "")).strip()
    profile_ids = {profile["id"] for profile in profiles}
    if active_profile_id not in profile_ids:
        active_profile_id = profiles[0]["id"] if profiles else ""

    return {
        "active_profile_id": active_profile_id,
        "profiles": profiles,
    }


def validate_profile(
    profile: Mapping[str, Any],
    existing_profiles: Sequence[Mapping[str, Any]] = (),
    editing_profile_id: str = "",
) -> dict:
    """Validate and normalize one profile before it enters the settings model."""
    name = str(profile.get("name", "")).strip()
    endpoint = str(profile.get("endpoint", "")).strip().rstrip("/")
    model = str(profile.get("model", "")).strip()
    api_key = str(profile.get("api_key", "")).strip()
    profile_id = str(profile.get("id", "")).strip() or new_profile_id()

    if not name:
        raise LLMProfileValidationError("Enter a profile name.")
    if not endpoint:
        raise LLMProfileValidationError("Enter an endpoint URL.")
    parsed_endpoint = urlparse(endpoint)
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.netloc:
        raise LLMProfileValidationError(
            "Enter a complete HTTP or HTTPS endpoint URL."
        )
    if not model:
        raise LLMProfileValidationError("Enter a model name.")

    duplicate = next(
        (
            existing
            for existing in existing_profiles
            if str(existing.get("id", "")) != editing_profile_id
            and str(existing.get("name", "")).strip().casefold() == name.casefold()
        ),
        None,
    )
    if duplicate is not None:
        raise LLMProfileValidationError(
            f'A profile named "{name}" already exists.'
        )

    return {
        "id": profile_id,
        "name": name,
        "endpoint": endpoint,
        "model": model,
        "api_key": api_key,
    }


def active_profile(ai_settings: Mapping[str, Any] | None) -> dict | None:
    normalized = normalize_ai_settings(ai_settings)
    active_id = normalized["active_profile_id"]
    return next(
        (
            deepcopy(profile)
            for profile in normalized["profiles"]
            if profile["id"] == active_id
        ),
        None,
    )


def _has_legacy_profile(source: Mapping[str, Any]) -> bool:
    return any(
        str(source.get(field, "")).strip()
        for field in ("endpoint", "model", "api_key")
    )


def _normalize_profiles(raw_profiles: Sequence[Any]) -> list[dict]:
    profiles = []
    seen_ids = set()
    seen_names = set()

    for index, raw_profile in enumerate(raw_profiles, start=1):
        if not isinstance(raw_profile, Mapping):
            continue

        profile_id = str(raw_profile.get("id", "")).strip()
        if not profile_id or profile_id in seen_ids:
            profile_id = new_profile_id()

        base_name = str(raw_profile.get("name", "")).strip() or f"Profile {index}"
        name = _unique_name(base_name, seen_names)
        profiles.append(
            {
                "id": profile_id,
                "name": name,
                "endpoint": str(raw_profile.get("endpoint", "")).strip(),
                "model": str(raw_profile.get("model", "")).strip(),
                "api_key": str(raw_profile.get("api_key", "")).strip(),
            }
        )
        seen_ids.add(profile_id)
        seen_names.add(name.casefold())

    return profiles


def _unique_name(name: str, seen_names: set[str]) -> str:
    if name.casefold() not in seen_names:
        return name

    suffix = 2
    while f"{name} {suffix}".casefold() in seen_names:
        suffix += 1
    return f"{name} {suffix}"
