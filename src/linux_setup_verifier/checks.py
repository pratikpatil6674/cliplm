"""Low-level Linux environment checks.

This module is focused on gathering facts about the host system.
- Probe: knows how to inspect the machine
- Verifier: knows how to interpret the probe results
- Notifier: knows how to present the results
"""

from __future__ import annotations

import os
import shutil
import subprocess
from ctypes.util import find_library

from .models import VerificationReport


class LinuxEnvironmentProbe:
    """Collects Linux setup information into a VerificationReport.

    The probe follows a simple builder-style flow:
    1. detect session type
    2. append shared-library checks
    3. append Wayland-specific executable/process checks

    The probe does not show UI and does not exit the process.
    """

    def build_report(self) -> VerificationReport:
        session_type = self.detect_session_type()
        report = VerificationReport(session_type=session_type)

        self._check_session_type(report)
        self._check_shared_lib(report, "Xcursor", "libXcursor")
        self._check_shared_lib(report, "xcb", "libxcb")
        self._check_any_shared_lib(report, ["xcb-cursor", "xcb_cursor"], "libxcb-cursor")

        if session_type == "wayland":
            self._check_executable(report, "ydotool", "ydotool", blocking=False)
            self._check_process(report, "ydotoold", "ydotoold", blocking=False)
            self._check_executable(report, "Xwayland", "Xwayland", blocking=True)

        return report

    def detect_session_type(self) -> str:
        """Best-effort session detection.

        We prefer XDG_SESSION_TYPE when present, then fall back to the common display
        environment variables. Returning "unknown" is intentional because it allows
        the caller to treat detection failure as a first-class error.
        """
        session_type = (os.environ.get("XDG_SESSION_TYPE") or "").strip().lower()
        if session_type in {"wayland", "x11"}:
            return session_type
        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        if os.environ.get("DISPLAY"):
            return "x11"
        return "unknown"

    def _check_session_type(self, report: VerificationReport) -> None:
        ok = report.session_type in {"wayland", "x11"}
        detail = report.session_type if ok else "Could not detect X11 or Wayland session"
        report.add_entry("Display session", ok, detail, blocking=True)

    def _check_shared_lib(self, report: VerificationReport, lib_name: str, display_name: str) -> None:
        found = find_library(lib_name) is not None
        detail = f"{display_name} available" if found else f"{display_name} not found"
        report.add_entry(display_name, found, detail, blocking=True)

    def _check_any_shared_lib(self, report: VerificationReport, lib_names: list[str], display_name: str) -> None:
        found_name = next((name for name in lib_names if find_library(name) is not None), None)
        found = found_name is not None
        detail = f"{display_name} available via {found_name}" if found else f"{display_name} not found"
        report.add_entry(display_name, found, detail, blocking=True)

    def _check_executable(
        self,
        report: VerificationReport,
        command_name: str,
        display_name: str,
        blocking: bool,
    ) -> None:
        path = self._find_executable_path(command_name)
        found = path is not None
        detail = path if found else f"{display_name} is not installed"
        report.add_entry(display_name, found, detail, blocking=blocking)

    def _check_process(
        self,
        report: VerificationReport,
        process_name: str,
        display_name: str,
        blocking: bool,
    ) -> None:
        try:
            result = subprocess.run(
                ["pgrep", "-x", process_name],
                check=False,
                capture_output=True,
                text=True,
            )
            running = result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            running = False

        detail = f"{display_name} is running" if running else f"{display_name} is not running"
        report.add_entry(display_name, running, detail, blocking=blocking)

    def _find_executable_path(self, command_name: str) -> str | None:
        """Resolve an executable path from the current runtime PATH."""
        return shutil.which(command_name)
