from __future__ import annotations

from PySide6.QtWidgets import QApplication


APP_STYLESHEET = r"""
* {
    color: #1d2938;
    font-size: 13px;
}

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
QMessageBox {
    background: #f3f6f9;
}

QLabel {
    background: transparent;
}

QToolTip {
    color: #ffffff;
    background: #243247;
    border: 1px solid #3c4c63;
    border-radius: 6px;
    padding: 5px 7px;
}

QPushButton {
    min-height: 30px;
    padding: 0 12px;
    color: #344257;
    background: #ffffff;
    border: 1px solid #d5dee9;
    border-radius: 8px;
    font-weight: 600;
}
QPushButton:hover {
    color: #1d2938;
    background: #f8fafc;
    border-color: #aebdce;
}
QPushButton:pressed {
    background: #edf2f7;
    border-color: #91a4b9;
}
QPushButton:disabled {
    color: #9aa5b3;
    background: #eef2f6;
    border-color: #e1e6ec;
}
QPushButton#page_primary_action,
QPushButton#save_button,
QPushButton#primary_button,
QPushButton#update_download_button,
QPushButton[role="primary"] {
    color: #ffffff;
    background: #316bce;
    border-color: #316bce;
}
QPushButton#page_primary_action:hover,
QPushButton#save_button:hover,
QPushButton#primary_button:hover,
QPushButton#update_download_button:hover,
QPushButton[role="primary"]:hover {
    background: #285eb9;
    border-color: #285eb9;
}
QPushButton#danger_button,
QPushButton[role="danger"] {
    color: #b43d4b;
    background: #ffffff;
    border-color: #e8c8cd;
}
QPushButton#danger_button:hover,
QPushButton[role="danger"]:hover {
    color: #9e2f3d;
    background: #fff4f5;
    border-color: #ddaeb5;
}

QMessageBox QPushButton[role="danger"] {
    color: #ffffff;
    background: #dc2626;
    border-color: #dc2626;
}
QMessageBox QPushButton[role="danger"]:hover {
    color: #ffffff;
    background: #b91c1c;
    border-color: #b91c1c;
}
QToolButton {
    color: #59687b;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 0;
}
QToolButton:hover {
    color: #263448;
    background: #e8eff8;
    border-color: #dce6f2;
}
QToolButton:pressed {
    background: #dae5f2;
}

QLineEdit,
QPlainTextEdit,
QTextEdit,
QComboBox {
    color: #263448;
    background: #ffffff;
    border: 1px solid #d2dce7;
    border-radius: 8px;
    padding: 7px 10px;
    selection-color: #ffffff;
    selection-background-color: #316bce;
}
QLineEdit:hover,
QPlainTextEdit:hover,
QTextEdit:hover,
QComboBox:hover {
    border-color: #afbdcc;
}
QLineEdit:focus,
QPlainTextEdit:focus,
QTextEdit:focus,
QComboBox:focus {
    background: #ffffff;
    border-color: #316bce;
}
QLineEdit:disabled,
QPlainTextEdit:disabled,
QTextEdit:disabled,
QComboBox:disabled {
    color: #929eac;
    background: #eef2f6;
    border-color: #e0e6ed;
}
QComboBox {
    min-height: 28px;
    padding-right: 28px;
}
QComboBox::drop-down {
    width: 26px;
    border: none;
}
QComboBox QAbstractItemView {
    color: #263448;
    background: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-color: #214f96;
    selection-background-color: #e5eefc;
}

QCheckBox {
    color: #435166;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background: #ffffff;
    border: 1px solid #aebccc;
    border-radius: 5px;
}
QCheckBox::indicator:hover {
    border-color: #668ac1;
}
QCheckBox::indicator:checked {
    background: #316bce;
    border-color: #316bce;
}

QScrollArea,
QScrollArea > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    width: 9px;
    margin: 2px;
    background: transparent;
}
QScrollBar::handle:vertical {
    min-height: 34px;
    background: #c0cbd8;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #98a9bc;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    height: 0;
    background: transparent;
}
QScrollBar:horizontal {
    height: 9px;
    margin: 2px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    min-width: 34px;
    background: #c0cbd8;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #98a9bc;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    width: 0;
    background: transparent;
}

QMenu {
    color: #263448;
    background: #ffffff;
    border: 1px solid #cfd9e4;
    border-radius: 9px;
    padding: 5px;
}
QMenu::item {
    min-height: 20px;
    margin: 1px;
    padding: 6px 24px 6px 10px;
    border-radius: 6px;
}
QMenu::item:selected {
    color: #214f96;
    background: #e8f0fc;
}
QMenu::item:disabled {
    color: #a3acb8;
}
QMenu::separator {
    height: 1px;
    margin: 5px 7px;
    background: #e3e8ee;
}

QMenu::indicator {
    width: 14px;
    height: 14px;
    margin-left: 3px;
    background: #ffffff;
    border: 1px solid #aebccc;
    border-radius: 4px;
}
QMenu::indicator:unchecked:selected {
    background: #ffffff;
    border-color: #668ac1;
}
QMenu::indicator:checked {
    background: #316bce;
    border-color: #316bce;
}

QFrame#sidebar_tabs {
    background: #f8fafc;
    border: none;
    border-right: 1px solid #dfe6ee;
}
QFrame#content_shell,
QStackedWidget#sidebar_pages {
    border: none;
}
QToolButton#sidebar_tab_button {
    color: #68778a;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 3px 0 1px 0;
    font-size: 9px;
    font-weight: 600;
}
QToolButton#sidebar_tab_button:hover {
    color: #315c9d;
    background: #eaf1fb;
    border-color: #e0e9f5;
}
QToolButton#sidebar_tab_button:checked {
    color: #ffffff;
    background: #316bce;
    border-color: #316bce;
}
QFrame#update_badge {
    background: #df8a22;
    border: 2px solid #f8fafc;
    border-radius: 4px;
}

QFrame#page_header {
    background: #f3f6f9;
    border: none;
    border-bottom: 1px solid #dde4ec;
}
QLabel#page_title {
    color: #1e2b3b;
    font-size: 18px;
    font-weight: 700;
}
QLabel#page_count {
    color: #657487;
    background: #e7ecf2;
    border-radius: 9px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
}
QLineEdit#page_search {
    min-height: 30px;
    padding: 0 9px;
}
QPushButton#page_primary_action {
    min-height: 30px;
}
QToolButton#page_overflow_button {
    font-size: 18px;
    font-weight: 700;
}

QListWidget#clipboard_list,
QListWidget#favorites_list,
QListWidget#notes_list {
    color: #263448;
    background: #f3f6f9;
    border: none;
    padding: 2px 3px 6px 3px;
    outline: none;
}
QListWidget#clipboard_list::item,
QListWidget#favorites_list::item,
QListWidget#notes_list::item {
    margin: 4px 5px;
    padding: 0;
    border: none;
}
QFrame#clipboard_card,
QFrame#favorite_card,
QFrame#manual_card {
    color: #263448;
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 11px;
}
QFrame#clipboard_card:hover,
QFrame#favorite_card:hover,
QFrame#manual_card:hover {
    background: #fbfdff;
    border-color: #8da9cf;
}
QFrame#clipboard_card QLabel,
QFrame#favorite_card QLabel,
QFrame#manual_card QLabel,
QLabel#clip_preview {
    color: #243247;
    background: transparent;
    border: none;
}
QToolButton#card_action,
QPushButton#card_action {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
}
QToolButton#card_action:hover,
QPushButton#card_action:hover {
    background: #e9f0fa;
    border-color: #dce7f4;
}
QToolButton#card_action[role="danger"]:hover,
QPushButton#card_action[role="danger"]:hover {
    background: #fff0f2;
    border-color: #f0d4d8;
}
QToolButton#placeholder,
QPushButton#placeholder {
    background: transparent;
    border: none;
}
QLabel#manual_card_top {
    color: #748195;
    font-size: 10px;
    font-weight: 600;
}
QLabel#manual_card_bottom {
    color: #243247;
    font-size: 13px;
}

QWidget#ai_prompt_tab QFrame#sidebar {
    background: #f8fafc;
    border: none;
    border-right: 1px solid #dfe6ee;
}
QWidget#ai_prompt_tab QFrame#card {
    background: #ffffff;
    border: none;
}
QLabel#section_label,
QLabel#field_label {
    color: #667487;
    font-size: 11px;
    font-weight: 700;
}
QLabel#section_label {
    letter-spacing: 0.3px;
}
QLabel#section_label[hasContent="true"] {
    color: #3478e5;
}
QListWidget#prompts_list {
    color: #263448;
    background: #ffffff;
    border: none;
    border-radius: 0;
    padding: 4px;
    outline: none;
}
QFrame#prompts_header {
    background: #ffffff;
    border: none;
}
QListWidget#prompts_list::item {
    min-height: 30px;
    margin: 1px 0;
    padding: 0 2px;
    border-radius: 6px;
}
QListWidget#prompts_list::item:hover {
    background: #f0f4f9;
}
QListWidget#prompts_list::item:selected {
    color: #214f96;
    background: #e4edfb;
}
QWidget#prompt_list_row {
    background: transparent;
    border: none;
}

QLabel#prompt_list_name {
    background: transparent;
    border: none;
    padding: 0;
}

QToolButton#prompt_actions_button {
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#ai_input_prompt,
QLabel#ai_output_text {
    color: #263448;
    background: #f9fbfd;
    border: 1px solid #dbe3ec;
    border-radius: 9px;
    padding: 9px 11px;
}
QFrame#prompt_context_card,
QFrame#input_context_card {
    background: transparent;
    border: none;
}
QLabel#prompt_summary,
QLabel#input_summary,
QLabel#ai_request_status,
QLabel#ai_request_state {
    color: #6b7788;
    font-size: 11px;
}
QFrame#context_summary_row {
    background: transparent;
    border: none;
}
QLabel#prompt_summary[contextHovered="true"],
QLabel#input_summary[contextHovered="true"] {
    color: #172233;
}
QWidget#input_data_placeholder,
QScrollArea#ai_input_scroll {
    color: #263448;
    background: transparent;
    border: none;
}
QLabel#ai_input_prompt,
QWidget#input_data_placeholder {
    background: #f4f8ff;
    border: 1px solid #c9daf5;
    border-radius: 8px;
    padding: 7px 9px;
}
QLabel#ai_request_state[state="complete"] {
    color: #4c8a67;
    font-weight: 700;
}
QLabel#ai_request_state[state="failed"] {
    color: #b44b55;
    font-weight: 700;
}
QLabel#section_label[llmState="running"] {
    color: #3478e5;
}
QLabel#section_label[llmState="complete"] {
    color: #4c8a67;
}
QLabel#section_label[llmState="failed"] {
    color: #b44b55;
}

QLabel#ai_output_text {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0;
}
QScrollArea#ai_output_scroll {
    background: transparent;
    border: none;
    border-bottom: 1px solid #dbe3ec;
}
QFrame#output_card {
    background: transparent;
    border: none;
}
QFrame#output_actions_container {
    background: transparent;
    border: none;
}
QToolButton#open_prompts_store_button,
QToolButton#reload_prompts_button {
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
}
QToolButton#output_action_button {
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
}

QWidget#translate_tab QFrame#controls {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #dde4ec;
}
QWidget#translate_tab QFrame#card {
    background: #f3f6f9;
    border: none;
}
QComboBox#language_combo {
    min-height: 30px;
    background: #f9fbfd;
}
QToolButton#reverse_language_button {
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}
QPushButton#translate_button {
    min-height: 32px;
    padding: 0;
    color: #ffffff;
    background: #316bce;
    border-color: #316bce;
}
QPushButton#translate_button QLabel#translate_action_label {
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#translate_button QLabel#translate_provider_label {
    color: #ffffff;
    font-size: 10px;
    font-weight: 500;
}
QPushButton#translate_button:hover {
    background: #285eb9;
    border-color: #285eb9;
}
QFrame#translation_source_panel,
QFrame#translation_destination_panel {
    color: #263448;
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 10px;
    padding: 0;
    font-size: 13px;
}
QPlainTextEdit#translate_src_text,
QLabel#translated_text {
    color: #263448;
    background: transparent;
    border: none;
    border-radius: 9px;
    padding: 11px;
    font-size: 13px;
}

QWidget#settings_tab QFrame#card {
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 12px;
}
QLabel#card_title {
    color: #1f2d3d;
    font-size: 16px;
    font-weight: 700;
}
QLabel#settings_card_title {
    color: #1f2d3d;
    font-size: 12px;
    font-weight: 700;
}
QLabel#hint_label {
    color: #5f6e81;
    background: #f2f6fb;
    border: 1px solid #e0e8f2;
    border-radius: 8px;
    padding: 9px 11px;
}
QLineEdit#text_input,
QComboBox#text_input {
    background: #f9fbfd;
}
QWidget#settings_tab QLineEdit#text_input {
    min-height: 34px;
    padding: 0 10px;
}
QPushButton#manage_profiles_button {
    min-width: 72px;
    min-height: 34px;
    padding: 0 12px;
    color: #285eb9;
    background: #edf4ff;
    border-color: #c9daf5;
}
QPushButton#manage_profiles_button:hover {
    color: #1f4f9f;
    background: #e1ecff;
    border-color: #a9c4ee;
}


QFrame#llm_profile_summary,
QFrame#llm_profile_details {
    background: #f2f6fb;
    border: 1px solid #e0e8f2;
    border-radius: 9px;
}
QLabel#profile_summary_caption {
    color: #718096;
    font-size: 11px;
    font-weight: 700;
}
QLabel#profile_summary_value,
QLabel#profile_detail {
    color: #344257;
}
QLabel#dialog_heading {
    color: #1f2d3d;
    font-size: 17px;
    font-weight: 700;
}
QLabel#dialog_description {
    color: #66758a;
}
QLabel#validation_error {
    color: #b42318;
    background: #fff1f0;
    border: 1px solid #f3c4c0;
    border-radius: 7px;
    padding: 7px 9px;
}
QListWidget#llm_profile_list {
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 9px;
    padding: 4px;
    outline: none;
}
QListWidget#llm_profile_list::item {
    min-height: 30px;
    padding: 2px 8px;
    border-radius: 6px;
}
QListWidget#llm_profile_list::item:hover {
    background: #f2f6fb;
}
QListWidget#llm_profile_list::item:selected {
    color: #2458aa;
    background: #e6efff;
}
QDialog#llm_profile_manager_dialog QLineEdit {
    min-height: 32px;
}

QDialog#prompt_editor_dialog QFrame#sidebar,
QDialog#prompt_editor_dialog QFrame#card {
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 11px;
}
QDialog#manual_entry_dialog QLineEdit,
QDialog#manual_entry_dialog QPlainTextEdit,
QDialog#prompt_editor_dialog QLineEdit,
QDialog#prompt_editor_dialog QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #d2dce7;
}

QDialog#manual_entry_dialog QLineEdit:hover,
QDialog#manual_entry_dialog QPlainTextEdit:hover,
QDialog#prompt_editor_dialog QLineEdit:hover,
QDialog#prompt_editor_dialog QPlainTextEdit:hover {
    border-color: #afbdcc;
}
QDialog#manual_entry_dialog QLineEdit:focus,
QDialog#manual_entry_dialog QPlainTextEdit:focus,
QDialog#prompt_editor_dialog QLineEdit:focus,
QDialog#prompt_editor_dialog QPlainTextEdit:focus {
    background: #ffffff;
    border-color: #316bce;
}

QFrame#update_status_card {
    background: #ffffff;
    border: 1px solid #d8e0e9;
    border-radius: 11px;
}
QLabel#update_dialog_heading {
    color: #1e2b3b;
    font-size: 19px;
    font-weight: 700;
}
QLabel#update_status_title {
    color: #243247;
    font-size: 15px;
    font-weight: 700;
}
QFrame#update_version_card {
    background: #f2f5f8;
    border: none;
    border-radius: 8px;
}
QLabel#update_version_label {
    color: #7a8798;
    font-size: 10px;
    font-weight: 700;
}
QLabel#update_version_value {
    color: #243247;
    font-size: 15px;
    font-weight: 700;
}
QLabel#update_details {
    color: #405066;
}
QLabel#update_meta {
    color: #748195;
    font-size: 11px;
}
QLabel#update_status_pill {
    border: none;
    border-radius: 10px;
    padding: 0 8px;
    font-size: 10px;
    font-weight: 700;
}
QLabel#update_status_pill[state="idle"] {
    color: #536174;
    background: #e8edf3;
}
QLabel#update_status_pill[state="checking"] {
    color: #245d9f;
    background: #e5effb;
}
QLabel#update_status_pill[state="available"] {
    color: #92550b;
    background: #fff0d8;
}
QLabel#update_status_pill[state="current"] {
    color: #267047;
    background: #e3f3e9;
}
QLabel#update_status_pill[state="error"] {
    color: #a13b48;
    background: #fbe9ec;
}
"""


def apply_app_theme(app: QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
