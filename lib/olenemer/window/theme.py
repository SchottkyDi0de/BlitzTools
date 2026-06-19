from __future__ import annotations

PANEL_BG = "#242424"
PANEL_BG_RGBA = (36, 36, 36, 255)
ACCENT_BORDER_WIDTH = 1
ROW_SKIN_OPACITY = 0.5
ROW_SKIN_DARKEN = 0.42
BACKGROUND_IMAGE_OPACITY = 0.58
BACKGROUND_IMAGE_DARKEN = 0.32
BACKGROUND_IMAGE_BLUR_RADIUS = 1.0
ALLIES_TITLE_COLOR = "#00ff00"
ENEMIES_TITLE_COLOR = "#ff4444"
TITLE_PADDING_X = 8
AVATAR_IMAGE_WIDTH = 26
AVATAR_IMAGE_HEIGHT = 18
PLATOON_PENTAGON_RADIUS = 8
PLATOON_BADGE_OUTLINE = "#ffffff"
PLATOON_BADGE_TEXT_COLOR = "#FFFFFF"
WINDOW_TITLE_PREFIX = "Оленемер"

BASE_COLUMN_WIDTHS = {
    "avatar": 36,
    "platoon": 20,
    "nickname": 200,
    "tank": 150,
    "battles": 56,
    "winrate": 56,
    "damage": 52,
    "rating": 56,
}

BASE_TABLE_WIDTH = 600
ROW_HEIGHT = 26
HEADER_HEIGHT = 22
SUMMARY_HEIGHT = 30
TITLE_HEIGHT = 24

_ACCENT_HEX_BY_THEME = {
    "dark": "#00f0ff",
    "light": "#008c9e",
}


def accent_color_hex(theme: str = "dark") -> str:
    return _ACCENT_HEX_BY_THEME.get(theme, _ACCENT_HEX_BY_THEME["dark"])
