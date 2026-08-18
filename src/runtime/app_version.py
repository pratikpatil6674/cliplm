import os
from pathlib import Path
import re

try:
    from AppBuildVersion import APP_VERSION as BUILD_VERSION
except ImportError:
    BUILD_VERSION = ""


def _resolve_app_version() -> str:
    override = os.environ.get("CLIPLM_APP_VERSION", "").strip()
    if override:
        return override

    if BUILD_VERSION:
        return BUILD_VERSION

    try:
        project_text = (
            Path(__file__).resolve().parent.parent / "pyproject.toml"
        ).read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', project_text, re.MULTILINE)
        if match:
            return match.group(1)
    except OSError:
        pass

    return "Unknown"


APP_VERSION = _resolve_app_version()
