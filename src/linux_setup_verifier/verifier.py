"""High-level orchestration for Linux setup verification.

This module is the coordination layer.
It applies the Dependency Inversion Principle by depending on abstractions of
behavior rather than mixing raw probing and UI code together:

- LinuxEnvironmentProbe gathers facts
- notifiers present facts
- LinuxSetupVerifier decides which notifier to use and whether startup continues
"""

from __future__ import annotations

import sys

from .checks import LinuxEnvironmentProbe
from .models import VerificationReport
from .notifiers import NonQtNotifier, QtHelperNotifier


class LinuxSetupVerifier:
    """Coordinates verification, classification, and notification.

    This class is intentionally thin: it should read more like policy than plumbing.
    """

    def __init__(
        self,
        probe: LinuxEnvironmentProbe | None = None,
        qt_notifier: QtHelperNotifier | None = None,
        non_qt_notifier: NonQtNotifier | None = None,
    ):
        self.probe = probe or LinuxEnvironmentProbe()
        self.qt_notifier = qt_notifier or QtHelperNotifier()
        self.non_qt_notifier = non_qt_notifier or NonQtNotifier()

    def verify(self, parent=None) -> bool:
        """Run the Linux startup preflight.

        Returns:
            True when startup may continue.
            False when blocking failures were found.
        """
        if sys.platform != "linux":
            return True

        report = self.probe.build_report()

        if report.has_blocking_failures:
            self._notify_failure(report)
            return False

        if report.has_warnings:
            self._notify_warning(report)

        return True

    def _notify_failure(self, report: VerificationReport) -> None:
        title = "ClipLM Linux Setup Check"
        summary = "ClipLM cannot start because required Linux system components are missing."

        # Design rule:
        # - X11/shared stack failures should avoid Qt when possible.
        # - Wayland may use a helper-process Qt dialog because the main process will exit.
        if report.session_type == "x11":
            self.non_qt_notifier.notify(title, summary, report)
            return

        self.qt_notifier.notify(title, summary, "error", report)

    def _notify_warning(self, report: VerificationReport) -> None:
        title = "ClipLM Wayland Notice"
        summary = (
            "ClipLM can start, but automatic paste is unavailable on Wayland because ydotool or ydotoold is missing. "
            "You can still copy items and paste them manually."
        )

        # The app must still switch to xcb after verification, so warning-only notifications
        # should stay out of the main Qt process. On Wayland we still want the better design,
        # so we use the Qt helper subprocess rather than constructing a Qt app in-process.
        if report.session_type == "wayland":
            self.qt_notifier.notify(title, summary, "warning", report)
            return

        self.non_qt_notifier.notify(title, summary, report)


def verify_linux_system_setup(parent=None) -> bool:
    """Compatibility entrypoint used by the rest of the application."""
    _ = parent
    return LinuxSetupVerifier().verify(parent=parent)
