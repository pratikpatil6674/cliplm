from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
import platform
from typing import Any

from packaging.version import InvalidVersion, Version
from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)


logger = logging.getLogger(__name__)

UPDATE_MANIFEST_URL = (
    "https://packages.cliplm.org/updates/v1/stable.json"
)
DOWNLOAD_PAGE_URL = "https://www.cliplm.org/downloads/"
MAX_MANIFEST_BYTES = 256 * 1024
REQUEST_TIMEOUT_MS = 8_000

PACKAGE_LABELS = {
    "appimage": "AppImage",
    "deb": "DEB",
    "dmg": "DMG",
    "flatpak": "Flatpak",
    "homebrew": "Homebrew",
    "inno": "Windows installer",
    "msix": "MSIX",
    "rpm": "RPM",
    "snap": "Snap",
    "winget": "Winget",
}


class UpdateManifestError(ValueError):
    pass


@dataclass(frozen=True)
class UpdateResult:
    current_version: str
    latest_version: str
    target: str
    channel: str
    generated_at: str
    available: bool
    summary: str = ""
    available_packages: tuple[str, ...] = ()


def current_platform_target() -> str:
    system = platform.system().casefold()
    machine = platform.machine().casefold()

    if machine in {"amd64", "x64", "x86_64"}:
        architecture = "x86_64"
    elif machine in {"aarch64", "arm64"}:
        architecture = "aarch64" if system == "linux" else "arm64"
    else:
        architecture = machine

    system_names = {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows",
    }
    normalized_system = system_names.get(system)
    if not normalized_system or not architecture:
        raise UpdateManifestError(
            f"Updates are not configured for {system or 'this platform'}."
        )
    return f"{normalized_system}-{architecture}"


def parse_update_manifest(
    payload: bytes | bytearray | str | dict[str, Any],
    current_version: str,
    target: str | None = None,
) -> UpdateResult:
    try:
        if isinstance(payload, (bytes, bytearray)):
            document = json.loads(bytes(payload).decode("utf-8"))
        elif isinstance(payload, str):
            document = json.loads(payload)
        else:
            document = payload
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateManifestError("The update response is not valid JSON.") from error

    if not isinstance(document, dict):
        raise UpdateManifestError("The update response has an invalid structure.")
    schema_version = document.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        raise UpdateManifestError("The update response uses an unsupported schema.")
    if document.get("product") != "cliplm":
        raise UpdateManifestError("The update response is for another product.")
    if document.get("channel") != "stable":
        raise UpdateManifestError("The update response is for another channel.")

    target_name = target or current_platform_target()
    targets = document.get("targets")
    target_data = targets.get(target_name) if isinstance(targets, dict) else None
    if not isinstance(target_data, dict):
        raise UpdateManifestError(
            f"No stable ClipLM release is listed for {target_name}."
        )

    latest_version = target_data.get("recommended_version")
    if not isinstance(latest_version, str) or not latest_version.strip():
        raise UpdateManifestError("The latest version is missing from the response.")
    latest_version = latest_version.strip()

    try:
        current_parsed = Version(current_version)
        latest_parsed = Version(latest_version)
    except InvalidVersion as error:
        raise UpdateManifestError("The update response contains an invalid version.") from error

    summary = _first_short_text(
        target_data.get("summary"),
        target_data.get("release_summary"),
        document.get("summary"),
        document.get("release_summary"),
    )
    generated_at = _short_text(document.get("generated_at"), 80)
    package_names = _available_package_names(target_data.get("packages"))

    return UpdateResult(
        current_version=current_version,
        latest_version=latest_version,
        target=target_name,
        channel="stable",
        generated_at=generated_at,
        available=latest_parsed > current_parsed,
        summary=summary,
        available_packages=package_names,
    )


def cached_update_result(
    current_version: str,
    settings: dict[str, Any],
) -> UpdateResult | None:
    latest_version = settings.get("last_known_version", "")
    target = settings.get("last_target", "")
    if not isinstance(latest_version, str) or not latest_version.strip():
        return None

    try:
        available = Version(latest_version) > Version(current_version)
    except InvalidVersion:
        return None

    packages = settings.get("last_available_packages", [])
    if not isinstance(packages, list):
        packages = []
    known_packages = tuple(
        package_name
        for package_name in packages
        if package_name in PACKAGE_LABELS
    )

    return UpdateResult(
        current_version=current_version,
        latest_version=latest_version,
        target=target if isinstance(target, str) else "",
        channel="stable",
        generated_at=_short_text(settings.get("last_generated_at"), 80),
        available=available,
        summary=_short_text(settings.get("last_summary"), 1_000),
        available_packages=known_packages,
    )


def is_update_check_due(
    last_checked_at: str,
    *,
    now: datetime | None = None,
    interval: timedelta = timedelta(hours=24),
) -> bool:
    if not last_checked_at:
        return True

    try:
        checked_at = datetime.fromisoformat(last_checked_at.replace("Z", "+00:00"))
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True

    current_time = now or datetime.now(timezone.utc)
    return current_time - checked_at >= interval


class UpdateService(QObject):
    checkingStarted = Signal()
    checkSucceeded = Signal(object)
    checkFailed = Signal(str)

    def __init__(self, current_version: str, parent: QObject | None = None):
        super().__init__(parent)
        self.current_version = current_version
        self.last_result: UpdateResult | None = None
        self.last_error = ""
        self.is_checking = False
        self._manager = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._response = bytearray()
        self._abort_reason = ""
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._handle_timeout)

    def check(self) -> None:
        if self.is_checking:
            return

        request = QNetworkRequest(QUrl(UPDATE_MANIFEST_URL))
        request.setRawHeader(b"Accept", b"application/json")
        request.setRawHeader(
            b"User-Agent",
            f"ClipLM/{self.current_version}".encode("ascii", errors="replace"),
        )
        request.setAttribute(
            QNetworkRequest.RedirectPolicyAttribute,
            QNetworkRequest.NoLessSafeRedirectPolicy,
        )
        request.setTransferTimeout(REQUEST_TIMEOUT_MS)

        self.is_checking = True
        self.last_error = ""
        self._response.clear()
        self._abort_reason = ""
        self.checkingStarted.emit()

        reply = self._manager.get(request)
        self._reply = reply
        reply.readyRead.connect(lambda: self._read_available(reply))
        reply.finished.connect(lambda: self._finish_request(reply))
        self._timeout.start(REQUEST_TIMEOUT_MS)

    def _read_available(self, reply: QNetworkReply) -> None:
        if reply is not self._reply or not reply.isOpen():
            return
        self._response.extend(bytes(reply.readAll()))
        if len(self._response) > MAX_MANIFEST_BYTES and not self._abort_reason:
            self._abort_reason = "The update response was unexpectedly large."
            reply.abort()

    def _handle_timeout(self) -> None:
        if self._reply is None:
            return
        self._abort_reason = "The update server did not respond in time."
        self._reply.abort()

    def _finish_request(self, reply: QNetworkReply) -> None:
        if reply is not self._reply:
            reply.deleteLater()
            return

        self._read_available(reply)
        self._timeout.stop()
        self._reply = None

        abort_reason = self._abort_reason
        network_error = reply.error()
        network_error_text = reply.errorString()
        status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        final_scheme = reply.url().scheme().casefold()
        reply.deleteLater()

        if abort_reason:
            self._fail(abort_reason)
            return
        if network_error != QNetworkReply.NoError:
            self._fail(f"Could not check for updates: {network_error_text}")
            return
        if status != 200:
            self._fail(f"The update server returned HTTP {status or 'error'}.")
            return
        if final_scheme != "https":
            self._fail("The update request was redirected to an insecure address.")
            return

        try:
            result = parse_update_manifest(
                bytes(self._response),
                self.current_version,
            )
        except UpdateManifestError as error:
            self._fail(str(error))
            return

        self.is_checking = False
        self.last_result = result
        self.last_error = ""
        self.checkSucceeded.emit(result)

    def _fail(self, message: str) -> None:
        self.is_checking = False
        self.last_error = message
        logger.warning(message)
        self.checkFailed.emit(message)


def _available_package_names(packages: Any) -> tuple[str, ...]:
    if not isinstance(packages, dict):
        return ()
    return tuple(
        package_name
        for package_name in PACKAGE_LABELS
        if isinstance(packages.get(package_name), dict)
        and packages[package_name].get("available") is True
    )


def _first_short_text(*values: Any) -> str:
    for value in values:
        text = _short_text(value, 1_000)
        if text:
            return text
    return ""


def _short_text(value: Any, maximum_length: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:maximum_length]
