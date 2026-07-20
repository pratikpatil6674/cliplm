"""Qt dialog rendering for Linux setup verification.

This module exists so Qt-related UI code stays isolated from the rest of the
verification logic. That helps in two ways:

1. X11 failures can use non-Qt notifiers without importing any Qt widgets.
2. Wayland can still use the richer in-app style via a helper process.

The dialog rendering is intentionally pure UI code.
"""

from __future__ import annotations

import json
from typing import Mapping

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)


def show_qt_dialog(payload: Mapping[str, str]) -> None:
    """Render a styled setup dialog from an in-memory payload.

    This function is intentionally module-level so it can be used as the target
    of a `multiprocessing` child process.
    """
    app = QApplication.instance() or QApplication([])

    title = payload["title"]
    summary = payload["summary"]
    severity = payload["severity"]
    details_html = payload["details_html"]

    dialog = QDialog()
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.resize(600, 500)

    accent = "#d14343" if severity == "error" else "#1a73e8"
    heading = "#7a1d1d" if severity == "error" else "#163a70"
    surface = "#fff7f7" if severity == "error" else "#f7fbff"

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)

    hero = QFrame()
    hero.setObjectName("hero")
    hero_layout = QVBoxLayout(hero)
    hero_layout.setContentsMargins(14, 14, 14, 14)
    hero_layout.setSpacing(6)

    title_label = QLabel(title)
    title_label.setObjectName("title_label")
    hero_layout.addWidget(title_label)

    summary_label = QLabel(summary)
    summary_label.setObjectName("summary_label")
    summary_label.setWordWrap(True)
    hero_layout.addWidget(summary_label)
    layout.addWidget(hero)

    details_card = QFrame()
    details_card.setObjectName("details_card")
    details_layout = QVBoxLayout(details_card)
    details_layout.setContentsMargins(14, 14, 14, 14)
    details_layout.setSpacing(8)

    details_label = QLabel("Environment Status")
    details_label.setObjectName("details_label")
    details_layout.addWidget(details_label)

    details_view = QTextEdit()
    details_view.setReadOnly(True)
    details_view.setHtml(details_html)
    details_view.setObjectName("details_view")
    details_layout.addWidget(details_view)
    layout.addWidget(details_card, 1)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok)
    buttons.accepted.connect(dialog.accept)
    layout.addWidget(buttons)

    dialog.setStyleSheet(
        f"""
        QDialog {{
            background: #f5f7fb;
            color: #1f2933;
        }}
        QFrame#hero, QFrame#details_card {{
            background: #ffffff;
            border: 1px solid rgba(30,36,44,0.08);
            border-radius: 12px;
        }}
        QFrame#hero {{
            background: {surface};
            border-color: {accent};
        }}
        QLabel#title_label {{
            color: {heading};
            font-size: 17px;
            font-weight: 700;
        }}
        QLabel#summary_label {{
            color: #344150;
            font-size: 13px;
        }}
        QLabel#details_label {{
            color: #52606d;
            font-size: 12px;
            font-weight: 700;
        }}
        QTextEdit#details_view {{
            background: #fbfdff;
            border: 1px solid rgba(30,36,44,0.08);
            border-radius: 10px;
            padding: 10px;
            font-size: 14px;
            color: #263238;
        }}
        QDialogButtonBox QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3a7ef7, stop:1 #2c62d6);
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            min-width: 88px;
            font-weight: 600;
        }}
        QDialogButtonBox QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4b88fb, stop:1 #3871e0);
        }}
        """
    )
    dialog.exec()
    app.quit()


def show_qt_dialog_from_payload(payload_path: str) -> None:
    """Render a styled setup dialog from a JSON payload.

    The helper process reads a simple payload file instead of importing large parts
    of the main app. That keeps the subprocess mode focused and stable.
    """
    with open(payload_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    show_qt_dialog(payload)
