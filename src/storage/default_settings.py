"""Default shape for persisted application settings.

SettingsStore deep-clones this mapping before merging user configuration. That
preserves newly introduced keys for existing users and prevents one controller
instance from mutating defaults observed by another test or application run.
"""

DEFAULT_SETTINGS = {
    "appearance": {
        "theme": "blue",
        "dark_mode": False,
    },
    "ai": {
        "active_profile_id": "",
        "profiles": [],
    },
    "translate": {
        "enabled": True,
        "source_language": "auto",
        "destination_language": "en",
        "api": "google",
    },
    "updates": {
        "check_automatically": True,
        "channel": "stable",
        "last_checked_at": "",
        "last_known_version": "",
        "last_target": "",
        "last_generated_at": "",
        "last_summary": "",
        "last_available_packages": [],
    },
}
