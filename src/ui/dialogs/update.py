from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.update_service import PACKAGE_LABELS, UpdateResult


class UpdateDialog(QDialog):
    checkRequested = Signal()
    downloadRequested = Signal()

    def __init__(self, current_version: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("update_dialog")
        self.current_version = current_version
        self.setWindowTitle("ClipLM updates")
        self.setModal(False)
        self.setMinimumWidth(480)
        self.setMaximumWidth(560)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._setup_ui()
        self.set_idle()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(8)

        self.status_card = QFrame()
        self.status_card.setObjectName("update_status_card")
        card_layout = QVBoxLayout(self.status_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        self.status_pill = QLabel()
        self.status_pill.setObjectName("update_status_pill")
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.status_pill.setFixedHeight(20)

        self.status_title = QLabel()
        self.status_title.setObjectName("update_status_title")
        self.status_title.setWordWrap(True)

        status_heading = QHBoxLayout()
        status_heading.setSpacing(8)
        status_heading.addWidget(self.status_title, 1)
        status_heading.addWidget(self.status_pill, 0, Qt.AlignTop)

        versions = QHBoxLayout()
        versions.setSpacing(8)
        installed_card, self.installed_value = self._version_card(
            "INSTALLED",
            self.current_version,
        )
        latest_card, self.latest_value = self._version_card(
            "LATEST",
            "Not checked",
        )
        versions.addWidget(installed_card, 1)
        versions.addWidget(latest_card, 1)

        self.details_label = QLabel()
        self.details_label.setObjectName("update_details")
        self.details_label.setTextFormat(Qt.PlainText)
        self.details_label.setWordWrap(True)

        self.meta_label = QLabel()
        self.meta_label.setObjectName("update_meta")
        self.meta_label.setTextFormat(Qt.PlainText)
        self.meta_label.setWordWrap(True)

        card_layout.addLayout(status_heading)
        card_layout.addLayout(versions)
        card_layout.addWidget(self.details_label)
        card_layout.addWidget(self.meta_label)
        root.addWidget(self.status_card)


        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.check_button = QPushButton("Check again")
        self.check_button.setObjectName("update_check_button")
        self.check_button.clicked.connect(self.checkRequested)

        self.download_button = QPushButton("Open download page")
        self.download_button.setObjectName("update_download_button")
        self.download_button.clicked.connect(self.downloadRequested)

        close_button = QPushButton("Close")
        close_button.setObjectName("update_close_button")
        close_button.clicked.connect(self.close)

        actions.addWidget(self.check_button)
        actions.addStretch(1)
        actions.addWidget(close_button)
        actions.addWidget(self.download_button)
        root.addLayout(actions)

    @staticmethod
    def _version_card(label: str, value: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("update_version_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(9, 5, 9, 5)
        layout.setSpacing(0)

        label_widget = QLabel(label)
        label_widget.setObjectName("update_version_label")
        value_widget = QLabel(value)
        value_widget.setObjectName("update_version_value")
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        return card, value_widget

    def set_idle(self) -> None:
        self._set_pill("NOT CHECKED", "idle")
        self.status_title.setText("Check for ClipLM updates")
        self.latest_value.setText("Not checked")
        self.details_label.setText(
            "ClipLM checks a small release manifest for your operating "
            "system and compares it with the installed version."
        )
        self.meta_label.setText("Stable channel")
        self._set_checking(False)

    def set_checking(self) -> None:
        self._set_pill("CHECKING", "checking")
        self.status_title.setText("Checking for updates...")
        self.latest_value.setText("Checking...")
        self.details_label.setText(
            "Contacting the ClipLM update service. No clipboard or account data "
            "is included in this request."
        )
        self.meta_label.setText("Stable channel")
        self._set_checking(True)

    def set_result(self, result: UpdateResult) -> None:
        self.installed_value.setText(result.current_version)
        self.latest_value.setText(result.latest_version)

        if result.available:
            self._set_pill("UPDATE AVAILABLE", "available")
            self.status_title.setText(
                f"ClipLM {result.latest_version} is available"
            )
            default_details = (
                "A newer stable release is ready. Open the download page to "
                "choose the installer for this computer."
            )
        else:
            self._set_pill("UP TO DATE", "current")
            self.status_title.setText("ClipLM is up to date")
            default_details = (
                "You are running the latest stable ClipLM release available "
                "for this computer."
            )

        self.details_label.setText(result.summary or default_details)
        self.meta_label.setText(self._result_metadata(result))
        self._set_checking(False)

    def set_error(self, message: str) -> None:
        self._set_pill("CHECK FAILED", "error")
        self.status_title.setText("ClipLM could not check for updates")
        self.latest_value.setText("Unavailable")
        self.details_label.setText(message)
        self.meta_label.setText(
            "You can still use the download page or try checking again."
        )
        self._set_checking(False)

    def _set_checking(self, checking: bool) -> None:
        self.check_button.setDisabled(checking)
        self.check_button.setText("Checking..." if checking else "Check again")

    def _set_pill(self, text: str, state: str) -> None:
        self.status_pill.setText(text)
        self.status_pill.setProperty("state", state)
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

    @staticmethod
    def _result_metadata(result: UpdateResult) -> str:
        parts = ["Stable channel"]
        if result.target:
            parts.append(result.target)
        if result.available_packages:
            package_text = ", ".join(
                PACKAGE_LABELS[name]
                for name in result.available_packages
                if name in PACKAGE_LABELS
            )
            if package_text:
                parts.append(f"Available: {package_text}")
        if result.generated_at:
            parts.append(f"Published: {result.generated_at}")
        return "  |  ".join(parts)

    def _set_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background: #f5f7fb;
            }
            QLabel {
                background: transparent;
                color: #202733;
            }
            QLabel#update_dialog_heading {
                font-size: 15pt;
                font-weight: 700;
            }
            QFrame#update_status_card {
                background: #ffffff;
                border: 1px solid #dce2eb;
                border-radius: 12px;
            }
            QLabel#update_status_title {
                color: #202733;
                font-size: 12pt;
                font-weight: 700;
            }
            QFrame#update_version_card {
                background: #f5f7fb;
                border: none;
                border-radius: 8px;
            }
            QLabel#update_version_label {
                color: #7a8595;
                font-size: 8pt;
                font-weight: 700;
            }
            QLabel#update_version_value {
                color: #202733;
                font-size: 12pt;
                font-weight: 700;
            }
            QLabel#update_details {
                color: #344054;
                font-size: 9pt;
            }
            QLabel#update_meta {
                color: #687386;
                font-size: 9pt;
            }
            QPushButton {
                min-height: 28px;
                border-radius: 7px;
                padding: 0 9px;
                font-size: 9pt;
                font-weight: 600;
                text-transform: none;
            }
            QPushButton#update_check_button,
            QPushButton#update_close_button {
                color: #344054;
                background: #ffffff;
                border: 1px solid #d5dce7;
            }
            QPushButton#update_check_button:hover,
            QPushButton#update_close_button:hover {
                background: #edf2f8;
            }
            QPushButton#update_check_button:disabled {
                color: #8c96a5;
                background: #eef1f5;
            }
            QPushButton#update_download_button {
                color: #ffffff;
                background: #2f6fe4;
                border: none;
            }
            QPushButton#update_download_button:hover {
                background: #255fc8;
            }
        """)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.accept()
