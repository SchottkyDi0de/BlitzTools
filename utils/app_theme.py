from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color
from kivymd.animation import MDAnimationTransition
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from lib.config.handler import ConfigHandler

THEME_ANIM_DURATION = 0.22

_theme_animating = False

DARK_PALETTE = {
    "bg": (0.039, 0.055, 0.078, 1),
    "bg_panel": (0.031, 0.043, 0.063, 1),
    "accent": (0, 0.941, 1, 1),
    "accent_dim": (0, 0.941, 1, 0.28),
    "accent_glow": (0, 0.941, 1, 0.08),
    "surface": (0.05, 0.075, 0.11, 0.92),
    "text": (0.78, 0.86, 0.92, 1),
    "muted": (0.42, 0.5, 0.58, 1),
    "success": (0.2, 0.95, 0.55, 1),
}

LIGHT_PALETTE = {
    "bg": (0.92, 0.94, 0.96, 1),
    "bg_panel": (0.86, 0.89, 0.93, 1),
    "accent": (0, 0.55, 0.62, 1),
    "accent_dim": (0, 0.55, 0.62, 0.35),
    "accent_glow": (0, 0.55, 0.62, 0.1),
    "surface": (0.97, 0.98, 0.99, 0.95),
    "text": (0.12, 0.16, 0.22, 1),
    "muted": (0.38, 0.44, 0.52, 1),
    "success": (0.1, 0.65, 0.35, 1),
}

_ALL_PALETTES = (DARK_PALETTE, LIGHT_PALETTE)

_COLOR_PROPS = (
    "md_bg_color",
    "text_color",
    "icon_color",
    "line_color",
    "md_bg_color_disabled",
)

_SCROLL_TYPES = frozenset({"MDScrollView", "ScrollView"})
_TRANSPARENT = (0, 0, 0, 0)


def _explicit_md_bg_types():
    from ui.widgets import (
        CustomTitleBar,
        FuturaNavButton,
        SettingsOptionButton,
    )

    return (
        CustomTitleBar,
        FuturaNavButton,
        SettingsOptionButton,
    )


def _should_update_md_bg(widget) -> bool:
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.screenmanager import MDScreenManager
    from ui.main import MainLayout

    if isinstance(widget, MDLabel):
        return False
    if isinstance(widget, (MDScreen, MDScreenManager, MainLayout)):
        return True
    if isinstance(widget, MDBoxLayout):
        return isinstance(widget, _explicit_md_bg_types())
    return False


def get_palette(theme: str) -> dict[str, tuple]:
    return LIGHT_PALETTE if theme == "light" else DARK_PALETTE


def is_theme_animating() -> bool:
    return _theme_animating


def _lerp_color(a, b, t: float):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


lerp_color = _lerp_color


def _lerp_palette(old: dict, new: dict, t: float) -> dict[str, tuple]:
    return {key: _lerp_color(old[key], new[key], t) for key in new}


def _sync_label_render_colors(root) -> None:
    for widget in root.walk():
        if not isinstance(widget, MDLabel):
            continue
        if _is_inside_admin_notice(widget):
            continue
        if getattr(widget, "theme_text_color", None) != "Custom":
            continue
        if widget.text_color:
            widget.color = widget.text_color


def _sync_settings_options(root) -> None:
    from ui.widgets import SettingsOptionButton

    for widget in root.walk():
        if isinstance(widget, SettingsOptionButton):
            widget.sync_appearance()


def sync_feature_cards(root) -> None:
    from ui.widgets import FuturaFeatureCard

    for widget in root.walk():
        if isinstance(widget, FuturaFeatureCard):
            widget.sync_appearance()


_sync_feature_cards = sync_feature_cards


def _sync_status_dot(root, palette: dict) -> None:
    from ui.widgets import StatusDot

    success = palette["success"]
    for widget in root.walk():
        if not isinstance(widget, StatusDot):
            continue
        widget._color.rgba = (success[0], success[1], success[2], widget.alpha)


def _finalize_theme_transition(app: MDApp, target_theme: str) -> None:
    new_palette = get_palette(target_theme)
    _update_app_palette(app, new_palette)
    Window.clearcolor = new_palette["bg"]
    if not app.root:
        return
    root = app.root
    _apply_shell_backgrounds(root, new_palette)
    _sync_nav_buttons(root, new_palette)
    _sync_titlebar_chrome(root, new_palette)
    _sync_settings_options(root)
    _sync_status_dot(root, new_palette)
    sync_feature_cards(root)
    _clear_text_backgrounds(root)
    _sync_label_render_colors(root)
    sync_icon_colors(root, new_palette)
    _sync_admin_notice(root)

    def _resync_cards(_dt):
        if app.root:
            sync_feature_cards(app.root)

    Clock.schedule_once(_resync_cards, 0)
    Clock.schedule_once(_resync_cards, 0.12)


def _apply_interpolated_theme(app: MDApp, palette: dict) -> None:
    _update_app_palette(app, palette)
    Window.clearcolor = palette["bg"]
    if not app.root:
        return
    root = app.root
    _apply_shell_backgrounds(root, palette)
    _sync_nav_buttons(root, palette)
    _sync_titlebar_chrome(root, palette)
    _sync_settings_options(root)
    _sync_status_dot(root, palette)
    sync_feature_cards(root)
    _sync_label_render_colors(root)
    sync_icon_colors(root, palette)
    _sync_admin_notice(root)


def _animate_theme_transition(app: MDApp, target_theme: str) -> None:
    global _theme_animating

    old_palette = {key: tuple(value) for key, value in app.palette.items()}
    new_palette = get_palette(target_theme)
    start_time = Clock.get_boottime()

    app.theme_cls.theme_style = "Light" if target_theme == "light" else "Dark"
    _theme_animating = True

    def tick(_dt):
        global _theme_animating
        elapsed = Clock.get_boottime() - start_time
        raw_t = min(1.0, elapsed / THEME_ANIM_DURATION)
        t = MDAnimationTransition.out_cubic(raw_t)
        blended = _lerp_palette(old_palette, new_palette, t)
        _apply_interpolated_theme(app, blended)

        if raw_t >= 1.0:
            _theme_animating = False
            _finalize_theme_transition(app, target_theme)
            return False
        return True

    Clock.schedule_interval(tick, 0)


def _colors_equal(a, b, eps: float = 0.02) -> bool:
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(abs(x - y) <= eps for x, y in zip(a, b))


def _palette_key_for_color(color) -> str | None:
    if color is None:
        return None
    for palette in _ALL_PALETTES:
        for key, palette_color in palette.items():
            if _colors_equal(color, palette_color):
                return key
    return None


def _update_app_palette(app: MDApp, palette: dict) -> None:
    for key, value in palette.items():
        app.palette[key] = value


def _label_color_role(label: MDLabel) -> str:
    current = label.text_color
    key = _palette_key_for_color(current)
    if key in ("accent", "muted", "text"):
        return key
    if label.bold:
        return "accent"
    return "text"


def _is_inside_admin_notice(widget) -> bool:
    from ui.widgets import AdminNoticeBar

    seen: set[int] = set()
    parent = widget.parent
    depth = 0
    while parent is not None and id(parent) not in seen and depth < 32:
        if isinstance(parent, AdminNoticeBar):
            return True
        seen.add(id(parent))
        parent = parent.parent
        depth += 1
    return False


def _ensure_label_colors(root, palette: dict) -> None:
    for widget in root.walk():
        if not isinstance(widget, MDLabel):
            continue
        if _is_inside_admin_notice(widget):
            continue
        if getattr(widget, "theme_text_color", None) != "Custom":
            continue
        color = palette[_label_color_role(widget)]
        widget.text_color = color
        widget.color = color


def _clear_text_backgrounds(root) -> None:
    from ui.widgets import AdminNoticeBar

    for widget in root.walk():
        if isinstance(widget, AdminNoticeBar):
            continue
        if isinstance(widget, MDLabel):
            widget.canvas.before.remove_group("md-label-selection-color")
            widget.canvas.before.remove_group("md-label-selection-color-rectangle")
            widget._canvas_bg = None
            widget.md_bg_color = _TRANSPARENT
            if widget.text_color:
                widget.color = widget.text_color
            continue
        if isinstance(widget, MDBoxLayout) and not _should_update_md_bg(widget):
            widget.md_bg_color = _TRANSPARENT


def sync_icon_colors(root, palette: dict) -> None:
    from ui.widgets import FuturaNavButton, TitleBarButton, is_icon_widget

    titlebar = root.ids.titlebar
    titlebar_button_icon_ids: set[int] = set()

    for btn in titlebar.walk():
        if isinstance(btn, TitleBarButton):
            btn.sync_appearance()
            for child in btn.walk():
                if is_icon_widget(child):
                    titlebar_button_icon_ids.add(id(child))

    accent = palette["accent"]
    nav_icon_ids: set[int] = set()
    for btn in root.ids.nav_panel.walk():
        if not isinstance(btn, FuturaNavButton):
            continue
        for icon in btn.walk():
            if is_icon_widget(icon):
                nav_icon_ids.add(id(icon))
                icon.icon_color = accent

    for widget in root.walk():
        if not is_icon_widget(widget):
            continue
        if _is_inside_admin_notice(widget):
            continue
        if getattr(widget, "theme_icon_color", None) != "Custom":
            continue
        if id(widget) in titlebar_button_icon_ids or id(widget) in nav_icon_ids:
            continue
        widget.icon_color = accent

    _sync_admin_notice(root)


_ensure_icon_colors = sync_icon_colors


def _apply_shell_backgrounds(root, palette: dict) -> None:
    root.md_bg_color = palette["bg"]

    ids = root.ids
    ids.titlebar.md_bg_color = palette["bg_panel"]
    ids.nav_panel.md_bg_color = palette["bg_panel"]
    ids.screen_manager.md_bg_color = palette["bg"]
    ids.content_row.md_bg_color = palette["bg"]

    for screen in ids.screen_manager.screens:
        screen.md_bg_color = palette["bg"]
        screen.opacity = 1
        for widget in screen.walk():
            name = type(widget).__name__
            if name in _SCROLL_TYPES or name == "AnchorLayout":
                if hasattr(widget, "md_bg_color"):
                    widget.md_bg_color = palette["bg"]


def _fallback_bg_color(widget, current, theme: str, palette: dict):
    if current in ((0, 0, 0, 0), None):
        return None
    from ui.widgets import FuturaFeatureCard

    if isinstance(widget, FuturaFeatureCard):
        return None
    luminance = current[0] + current[1] + current[2]
    if theme == "light" and luminance < 0.45:
        if type(widget).__name__ == "FuturaFeatureCard":
            return palette["surface"]
        return palette["bg"]
    if theme == "dark" and luminance > 0.75:
        return palette["bg"]
    return None


def apply_palette_to_tree(root, new_palette: dict, *, theme: str) -> None:
    from ui.widgets import (
        FuturaFeatureCard,
        FuturaNavButton,
        SettingsOptionButton,
        TitleBarButton,
    )

    for widget in root.walk():
        if isinstance(widget, TitleBarButton):
            continue
        if _is_inside_admin_notice(widget):
            continue
        for prop in _COLOR_PROPS:
            if not hasattr(widget, prop):
                continue
            if isinstance(widget, FuturaFeatureCard) and prop in (
                "md_bg_color",
                "line_color",
            ):
                continue
            if isinstance(widget, SettingsOptionButton) and prop in (
                "md_bg_color",
                "line_color",
            ):
                continue
            if prop == "md_bg_color" and not _should_update_md_bg(widget):
                continue
            if prop == "icon_color":
                continue
            current = getattr(widget, prop)
            key = _palette_key_for_color(current)
            if key is not None:
                setattr(widget, prop, new_palette[key])
                continue
            if prop == "md_bg_color":
                fallback = _fallback_bg_color(widget, current, theme, new_palette)
                if fallback is not None:
                    setattr(widget, prop, fallback)

        if hasattr(widget, "_color") and hasattr(widget, "_sync_alpha"):
            key = _palette_key_for_color(widget._color.rgba)
            if key is not None:
                widget._color.rgba = new_palette[key]

        if isinstance(widget, (FuturaFeatureCard, FuturaNavButton, SettingsOptionButton)):
            continue

        for canvas in (widget.canvas, widget.canvas.before, widget.canvas.after):
            for instr in canvas.children:
                if not isinstance(instr, Color):
                    continue
                key = _palette_key_for_color(instr.rgba)
                if key is not None:
                    instr.rgba = new_palette[key]

    _ensure_label_colors(root, new_palette)
    sync_icon_colors(root, new_palette)
    _clear_text_backgrounds(root)
    sync_feature_cards(root)
    _sync_titlebar_chrome(root, new_palette)
    _sync_admin_notice(root)


def _sync_admin_notice(root) -> None:
    from ui.widgets import AdminNoticeBar

    bar = root.ids.get("admin_notice")
    if isinstance(bar, AdminNoticeBar):
        bar.sync_appearance()


def _sync_nav_buttons(root, palette: dict) -> None:
    from ui.widgets import FuturaNavButton

    for btn in root.ids.nav_panel.walk():
        if not isinstance(btn, FuturaNavButton):
            continue
        btn.sync_appearance()


def _sync_titlebar_chrome(root, palette: dict) -> None:
    from ui.widgets import ThemeToggleButton, TitleBarButton

    titlebar = root.ids.titlebar
    titlebar.md_bg_color = palette["bg_panel"]

    for widget in titlebar.walk():
        if isinstance(widget, ThemeToggleButton):
            widget.md_bg_color = _TRANSPARENT
        elif isinstance(widget, TitleBarButton):
            widget.sync_appearance()


def apply_theme_from_config(app: MDApp | None = None) -> str:
    app = app or MDApp.get_running_app()
    if not app:
        return "dark"

    theme = app.config.app_global.theme
    new_palette = get_palette(theme)
    app.theme_cls.theme_style = "Light" if theme == "light" else "Dark"
    _update_app_palette(app, new_palette)

    if app.root:
        apply_palette_to_tree(app.root, new_palette, theme=theme)
        _apply_shell_backgrounds(app.root, new_palette)
        _sync_nav_buttons(app.root, new_palette)
        _sync_titlebar_chrome(app.root, new_palette)

    Window.clearcolor = new_palette["bg"]
    return theme


def toggle_theme(app: MDApp | None = None) -> str:
    app = app or MDApp.get_running_app()
    if not app:
        return "dark"

    if _theme_animating:
        return app.config.app_global.theme

    ag = app.config.app_global
    ag.theme = "light" if ag.theme == "dark" else "dark"

    handler = ConfigHandler()
    handler.config = app.config
    handler.write_config()

    _animate_theme_transition(app, ag.theme)
    return ag.theme
