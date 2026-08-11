from PySide6.QtGui import QIcon

import resources_rc


def _icon(file_name: str) -> QIcon:
    return QIcon(f":/resources/icons/{file_name}")


APP_ICON = _icon("app.svg")

ADD_ICON_DARK = _icon("add_dark.svg")
ADD_ICON_LIGHT = _icon("add_light.svg")
AI_ICON = _icon("ai_dark.svg")
AI_ICON_LIGHT = _icon("ai_light.svg")
CLIP_ICON = _icon("clip_dark.svg")
CLIP_ICON_LIGHT = _icon("clip_light.svg")
COPY_ICON_DARK = _icon("copy_dark.svg")
COPY_ICON_LIGHT = _icon("copy_light.svg")
DELETE_ICON_DARK = _icon("delete_dark.svg")
EDIT_ICON_DARK = _icon("edit_dark.svg")
NOTE_ICON = _icon("note_dark.svg")
NOTE_ICON_LIGHT = _icon("note_light.svg")
SETTINGS_ICON = _icon("settings_dark.svg")
SETTINGS_ICON_LIGHT = _icon("settings_light.svg")
STAR_ICON = _icon("star_dark.svg")
STAR_ICON_LIGHT = _icon("star_light.svg")
SYNC_ICON_DARK = _icon("sync_dark.svg")
SYNC_ICON_LIGHT = _icon("sync_light.svg")
TRANSLATE_ICON = _icon("translate_dark.svg")
TRANSLATE_ICON_LIGHT = _icon("translate_light.svg")
UPDATE_ICON_DARK = _icon("update_dark.svg")
UPDATE_ICON_LIGHT = _icon("update_light.svg")

PASTE_ICON_DARK = _icon("clip_dark.svg")
PASTE_ICON_LIGHT = _icon("clip_light.svg")
