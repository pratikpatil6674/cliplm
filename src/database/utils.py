"""Small serialization and timestamp helpers shared by repositories."""

import datetime


def iso_now() -> str:
    """Return the UTC timestamp format already stored by ClipLM."""
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
