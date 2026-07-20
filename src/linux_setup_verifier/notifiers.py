"""Notification strategies for Linux setup verification.

This module uses a small Strategy-pattern style split:
- NonQtNotifier: terminal / zenity / kdialog path
- QtHelperNotifier: child-process Qt dialog path

The verifier chooses which notifier to use based on the report and the target
runtime constraints.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import shutil
import subprocess
import sys

from .models import VerificationReport
from .dialog import show_qt_dialog


class ReportFormatter:
    """Formats a VerificationReport for different notifier targets."""

    COLOR_MAP = {
        "OK": "#1f8f4d",
        "WARNING": "#d97706",
        "ERROR": "#d14343",
    }

    @classmethod
    def details_html(cls, report: VerificationReport) -> str:
        lines = []
        for entry in report.entries:
            color = cls.COLOR_MAP.get(entry.status, "#263238")
            lines.append(
                f'<div style="margin-bottom:8px; line-height:1.5;">'
                f'<span style="font-weight:700; color:#1f2933;">{entry.label}</span>: '
                f'<span style="font-weight:800; font-size:14px; color:{color};">{entry.status}</span> '
                f'<span style="color:#344150; font-size:14px;">- {entry.detail}</span>'
                f'</div>'
            )
        return "".join(lines)

    @staticmethod
    def details_plain(report: VerificationReport) -> str:
        return "\n".join(
            f"{entry.label}: {entry.status} - {entry.detail}"
            for entry in report.entries
        )


class NonQtNotifier:
    """Fallback notifier chain that does not depend on Qt.

    This path is important when the UI stack itself may be broken, especially on
    X11/XCB failures.
    """

    def notify(self, title: str, summary: str, report: VerificationReport) -> None:
        details = ReportFormatter.details_plain(report)
        full_message = f"{summary}\n\n{details}"
        self._print_to_console(title, summary, details)

        zenity = shutil.which("zenity")
        if zenity:
            result = subprocess.run(
                [zenity, "--error", "--title", title, "--width", "640", "--text", full_message],
                check=False,
            )
            if result.returncode in (0, 1):
                return

        kdialog = shutil.which("kdialog")
        if kdialog:
            result = subprocess.run(
                [kdialog, "--error", full_message, "--title", title],
                check=False,
            )
            if result.returncode in (0, 1):
                return

    @staticmethod
    def _print_to_console(title: str, summary: str, details: str) -> None:
        print(title, file=sys.stderr)
        print(summary, file=sys.stderr)
        print(details, file=sys.stderr)


class QtHelperNotifier:
    """Shows the styled Qt dialog in a dedicated child process.

    The child-process approach is the key design choice here:
    it lets Wayland use the richer Qt UI without contaminating the main process,
    which still needs to switch to `QT_QPA_PLATFORM=xcb` afterward.
    """

    def notify(self, title: str, summary: str, severity: str, report: VerificationReport) -> None:
        payload = {
            "title": title,
            "summary": summary,
            "severity": severity,
            "details_html": ReportFormatter.details_html(report),
        }
        details = ReportFormatter.details_plain(report)
        NonQtNotifier._print_to_console(title, summary, details)

        original_qt_platform = os.environ.get("QT_QPA_PLATFORM")

        try:
            # The child gets a clean environment and only the serializable payload.
            # This avoids the custom helper-argument plumbing while keeping the Qt
            # window isolated from the main process.
            os.environ.pop("QT_QPA_PLATFORM", None)
            ctx = mp.get_context("spawn")
            process = ctx.Process(target=show_qt_dialog, args=(payload,))
            process.start()
            process.join()
        except Exception:
            NonQtNotifier().notify(title, summary, report)
        finally:
            if original_qt_platform is not None:
                os.environ["QT_QPA_PLATFORM"] = original_qt_platform
            else:
                os.environ.pop("QT_QPA_PLATFORM", None)
