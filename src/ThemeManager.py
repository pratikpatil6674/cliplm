from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMenu

from AppTheme import APP_STYLESHEET
from AccentPalettes import (
    THEME_OPTIONS as ACCENT_THEME_OPTIONS,
    build_palette,
)


THEME_OPTIONS = (
    ("ClipLM Blue", "blue"),
    ("Inspiration Lime", "lime"),
)


_PALETTES = {
    ("blue", False): {
        "background": "#f3f6f9",
        "sidebar": "#f8fafc",
        "surface": "#ffffff",
        "surface_alt": "#f9fbfd",
        "raised": "#edf2f7",
        "text": "#263448",
        "strong": "#1d2938",
        "muted": "#667487",
        "border": "#d8e0e9",
        "border_strong": "#afbdcc",
        "accent": "#316bce",
        "accent_hover": "#285eb9",
        "accent_text": "#ffffff",
        "soft": "#e4edfb",
        "soft_text": "#214f96",
        "scrollbar": "#c0cbd8",
        "scrollbar_hover": "#98a9bc",
    },
    ("blue", True): {
        "background": "#101722",
        "sidebar": "#151e2b",
        "surface": "#172231",
        "surface_alt": "#131d2a",
        "raised": "#1d2a3a",
        "text": "#d9e2ee",
        "strong": "#f3f7fb",
        "muted": "#91a0b2",
        "border": "#2b3a4d",
        "border_strong": "#48627f",
        "accent": "#6ea2ff",
        "accent_hover": "#8ab5ff",
        "accent_text": "#101722",
        "soft": "#203553",
        "soft_text": "#a9c9ff",
        "scrollbar": "#3b4c62",
        "scrollbar_hover": "#526983",
    },
    ("lime", False): {
        "background": "#f4f6f1",
        "sidebar": "#e8ede7",
        "surface": "#ffffff",
        "surface_alt": "#f8faf7",
        "raised": "#edf2e9",
        "text": "#26312a",
        "strong": "#18211b",
        "muted": "#6f7c73",
        "border": "#d1dad2",
        "border_strong": "#9caaa0",
        "accent": "#779c2a",
        "accent_hover": "#688c20",
        "accent_text": "#ffffff",
        "soft": "#e7f0d7",
        "soft_text": "#52751a",
        "scrollbar": "#bdc8bf",
        "scrollbar_hover": "#98a69b",
    },
    ("lime", True): {
        "background": "#101713",
        "sidebar": "#17211b",
        "surface": "#141d18",
        "surface_alt": "#0f1612",
        "raised": "#1b251f",
        "text": "#dce3de",
        "strong": "#f5f7f5",
        "muted": "#91a098",
        "border": "#2b3931",
        "border_strong": "#526158",
        "accent": "#d6ff62",
        "accent_hover": "#e4ff91",
        "accent_text": "#111711",
        "soft": "#243128",
        "soft_text": "#d6ff62",
        "scrollbar": "#34433a",
        "scrollbar_hover": "#526158",
    },
}


THEME_OPTIONS = ACCENT_THEME_OPTIONS


class _MenuSurfacePolisher(QObject):
    def eventFilter(self, watched, event):
        if isinstance(watched, QMenu) and event.type() == QEvent.Polish:
            watched.setAttribute(Qt.WA_TranslucentBackground, True)
        return super().eventFilter(watched, event)


def _install_menu_surface_polisher(app: QApplication) -> None:
    if not hasattr(app, "_menu_surface_polisher"):
        polisher = _MenuSurfacePolisher(app)
        app.installEventFilter(polisher)
        app._menu_surface_polisher = polisher

    for widget in app.allWidgets():
        if isinstance(widget, QMenu):
            widget.setAttribute(Qt.WA_TranslucentBackground, True)


def normalize_theme_name(theme_name: str) -> str:
    supported = {value for _, value in THEME_OPTIONS}
    return theme_name if theme_name in supported else "blue"


def theme_stylesheet(theme_name: str, dark_mode: bool) -> str:
    theme_name = normalize_theme_name(theme_name)
    palette = build_palette(theme_name, dark_mode)
    p = palette
    return f"""
* {{
    font-family: "Inter", "Segoe UI", sans-serif;
    color: {p["text"]};
}}
QWidget#app_window,
QFrame#content_shell,
QStackedWidget#sidebar_pages,
QWidget#sidebar_page,
QWidget#clipboard_tab,
QWidget#favorites_tab,
QWidget#notes_tab,
QWidget#translate_tab,
QWidget#ai_prompt_tab,
QWidget#settings_tab,
QDialog,
QMessageBox {{
    background: {p["background"]};
}}
QToolTip {{
    color: {p["strong"]};
    background: {p["raised"]};
    border-color: {p["border_strong"]};
}}
QPushButton {{
    color: {p["text"]};
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QPushButton:hover {{
    color: {p["strong"]};
    background: {p["raised"]};
    border-color: {p["border_strong"]};
}}
QPushButton:pressed {{
    background: {p["soft"]};
    border-color: {p["border_strong"]};
}}
QPushButton:disabled {{
    color: {p["muted"]};
    background: {p["raised"]};
    border-color: {p["border"]};
}}
QPushButton#page_primary_action,
QPushButton#save_button,
QPushButton#primary_button,
QPushButton#update_download_button,
QPushButton#translate_button,
QPushButton[role="primary"] {{
    color: {p["accent_text"]};
    background: {p["accent"]};
    border-color: {p["accent"]};
}}
QPushButton#translate_button QLabel#translate_action_label,
QPushButton#translate_button QLabel#translate_provider_label {{
    color: {p["accent_text"]};
}}
QPushButton#page_primary_action:hover,
QPushButton#save_button:hover,
QPushButton#primary_button:hover,
QPushButton#update_download_button:hover,
QPushButton#translate_button:hover,
QPushButton[role="primary"]:hover {{
    color: {p["accent_text"]};
    background: {p["accent_hover"]};
    border-color: {p["accent_hover"]};
}}
QPushButton#danger_button,
QPushButton[role="danger"] {{
    color: #df7f8a;
    background: {p["surface"]};
    border-color: #74414a;
}}
QPushButton#danger_button:hover,
QPushButton[role="danger"]:hover {{
    color: #f39aa4;
    background: #3b2026;
    border-color: #8d4b56;
}}
QMessageBox QPushButton[role="danger"] {{
    color: #ffffff;
    background: #dc2626;
    border-color: #dc2626;
}}
QMessageBox QPushButton[role="danger"]:hover {{
    color: #ffffff;
    background: #b91c1c;
    border-color: #b91c1c;
}}
QToolButton {{
    color: {p["muted"]};
}}
QToolButton:hover {{
    color: {p["strong"]};
    background: {p["soft"]};
    border-color: {p["border"]};
}}
QToolButton:pressed {{
    background: {p["raised"]};
}}
QLineEdit,
QPlainTextEdit,
QTextEdit,
QComboBox {{
    color: {p["text"]};
    background: {p["surface_alt"]};
    border-color: {p["border"]};
    selection-color: {p["accent_text"]};
    selection-background-color: {p["accent"]};
}}
QLineEdit:hover,
QPlainTextEdit:hover,
QTextEdit:hover,
QComboBox:hover {{
    border-color: {p["border_strong"]};
}}
QLineEdit:focus,
QPlainTextEdit:focus,
QTextEdit:focus,
QComboBox:focus {{
    color: {p["strong"]};
    background: {p["surface"]};
    border-color: {p["accent"]};
}}
QLineEdit:disabled,
QPlainTextEdit:disabled,
QTextEdit:disabled,
QComboBox:disabled {{
    color: {p["muted"]};
    background: {p["raised"]};
    border-color: {p["border"]};
}}
QComboBox QAbstractItemView {{
    color: {p["text"]};
    background: {p["surface"]};
    border-color: {p["border"]};
    selection-color: {p["soft_text"]};
    selection-background-color: {p["soft"]};
}}
QCheckBox {{
    color: {p["text"]};
}}
QCheckBox::indicator {{
    background: {p["surface_alt"]};
    border-color: {p["border_strong"]};
}}
QCheckBox::indicator:hover {{
    border-color: {p["accent"]};
}}
QCheckBox::indicator:checked {{
    background: {p["accent"]};
    border-color: {p["accent"]};
}}
QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background: {p["scrollbar"]};
}}
QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{
    background: {p["scrollbar_hover"]};
}}
QMenu {{
    color: {p["text"]};
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QMenu::item:selected {{
    color: {p["soft_text"]};
    background: {p["soft"]};
}}
QMenu::item:disabled {{
    color: {p["muted"]};
}}
QMenu::separator {{
    background: {p["border"]};
}}

QMenu::indicator {{
    background: {p["surface_alt"]};
    border-color: {p["border_strong"]};
}}
QMenu::indicator:unchecked:selected {{
    background: {p["surface"]};
    border-color: {p["accent"]};
}}
QMenu::indicator:checked {{
    background: {p["accent"]};
    border-color: {p["accent"]};
}}
QFrame#sidebar_tabs {{
    background: {p["sidebar"]};
    border-right-color: {p["border"]};
}}
QToolButton#sidebar_tab_button {{
    color: {p["muted"]};
}}
QToolButton#sidebar_tab_button:hover {{
    color: {p["soft_text"]};
    background: {p["soft"]};
    border-color: {p["border"]};
}}
QToolButton#sidebar_tab_button:checked {{
    color: {p["accent_text"]};
    background: {p["accent"]};
    border-color: {p["accent"]};
}}
QFrame#update_badge {{
    background: #df8a22;
    border-color: {p["sidebar"]};
}}
QFrame#page_header {{
    background: {p["background"]};
    border-bottom-color: {p["border"]};
}}
QLabel#page_title,
QLabel#card_title,
QLabel#settings_card_title,
QLabel#update_dialog_heading,
QLabel#update_status_title,
QLabel#update_version_value {{
    color: {p["strong"]};
}}
QLabel#page_count,
QFrame#update_version_card {{
    color: {p["muted"]};
    background: {p["raised"]};
}}
QListWidget#clipboard_list,
QListWidget#favorites_list,
QListWidget#notes_list {{
    color: {p["text"]};
    background: {p["background"]};
}}
QFrame#clipboard_card,
QFrame#favorite_card,
QFrame#manual_card,
QWidget#settings_tab QFrame#card,
QFrame#update_status_card {{
    color: {p["text"]};
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QFrame#clipboard_card:hover,
QFrame#favorite_card:hover,
QFrame#manual_card:hover {{
    background: {p["surface_alt"]};
    border-color: {p["border_strong"]};
}}
QFrame#clipboard_card QLabel,
QFrame#favorite_card QLabel,
QFrame#manual_card QLabel,
QLabel#clip_preview,
QLabel#manual_card_bottom {{
    color: {p["text"]};
}}
QLabel#manual_card_top,
QLabel#section_label,
QLabel#field_label,
QLabel#update_meta,
QLabel#update_version_label {{
    color: {p["muted"]};
}}
QToolButton#card_action:hover,
QPushButton#card_action:hover {{
    background: {p["soft"]};
    border-color: {p["border"]};
}}
QWidget#ai_prompt_tab QFrame#sidebar {{
    background: {p["sidebar"]};
    border-right-color: {p["border"]};
}}
QWidget#ai_prompt_tab QFrame#card,
QWidget#translate_tab QFrame#controls {{
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QWidget#translate_tab QFrame#card {{
    background: {p["background"]};
}}
QListWidget#prompts_list,
QLabel#ai_output_text,
QFrame#translation_source_panel,
QFrame#translation_destination_panel,
QDialog#prompt_editor_dialog QFrame#sidebar,
QDialog#prompt_editor_dialog QFrame#card,
QDialog#manual_entry_dialog QLineEdit,
QDialog#manual_entry_dialog QPlainTextEdit,
QDialog#prompt_editor_dialog QLineEdit,
QDialog#prompt_editor_dialog QPlainTextEdit {{
    color: {p["text"]};
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QPlainTextEdit#translate_src_text,
QLabel#translated_text {{
    color: {p["text"]};
    background: transparent;
    border: none;
}}

QDialog#manual_entry_dialog QLineEdit:hover,
QDialog#manual_entry_dialog QPlainTextEdit:hover,
QDialog#prompt_editor_dialog QLineEdit:hover,
QDialog#prompt_editor_dialog QPlainTextEdit:hover {{
    border-color: {p["border_strong"]};
}}
QDialog#manual_entry_dialog QLineEdit:focus,
QDialog#manual_entry_dialog QPlainTextEdit:focus,
QDialog#prompt_editor_dialog QLineEdit:focus,
QDialog#prompt_editor_dialog QPlainTextEdit:focus {{
    background: {p["surface"]};
    border-color: {p["accent"]};
}}
QListWidget#prompts_list::item:hover {{
    background: {p["raised"]};
}}
QListWidget#prompts_list::item:selected {{
    color: {p["soft_text"]};
    background: {p["soft"]};
}}
QLabel#ai_input_prompt,
QWidget#input_data_placeholder {{
    color: {p["text"]};
    background: {p["surface_alt"]};
    border-color: {p["border"]};
}}
QFrame#output_actions_container {{
    background: {p["surface"]};
    border-color: {p["border"]};
}}
QComboBox#language_combo,
QLineEdit#text_input,
QComboBox#text_input {{
    color: {p["text"]};
    background: {p["surface_alt"]};
}}
QLabel#hint_label {{
    color: {p["muted"]};
    background: {p["raised"]};
    border-color: {p["border"]};
}}
QLabel#update_details {{
    color: {p["text"]};
}}
QLabel#update_status_pill[state="idle"] {{
    color: {p["muted"]};
    background: {p["raised"]};
}}
QLabel#update_status_pill[state="checking"] {{
    color: {p["soft_text"]};
    background: {p["soft"]};
}}
"""


def apply_app_theme(
    app: QApplication,
    theme_name: str = "blue",
    dark_mode: bool = False,
) -> None:
    app.setStyle("Fusion")
    _install_menu_surface_polisher(app)
    font = QFont("Inter")
    font.setPointSize(10)
    app.setFont(font)
    app.setProperty("themeName", normalize_theme_name(theme_name))
    app.setProperty("darkMode", bool(dark_mode))
    app.setStyleSheet(
        APP_STYLESHEET + theme_stylesheet(theme_name, dark_mode)
    )
