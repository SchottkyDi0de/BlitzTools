from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from utils import win_chrome
from utils.app_theme import is_theme_animating, lerp_color, toggle_theme
from utils.nav import navigate_to

HOVER_ANIM_DURATION = 0.2
ICON_TITLE_ICON_BLOCK = dp(26)
TITLE_WIDTH_SLACK = dp(6)
ICON_WIDGET_NAMES = frozenset({"MDIcon", "Icon"})
CARD_TITLE_BLOCK_HEIGHT = dp(30)
CARD_BODY_BLOCK_HEIGHT = dp(40)
CARD_CONTENT_SPACING = dp(6)


def is_icon_widget(widget) -> bool:
    return type(widget).__name__ in ICON_WIDGET_NAMES


def reset_progress_bar(fill) -> None:
    fill.size_hint_x = None
    fill.width = 0
    track = fill.parent
    if track is not None:
        track.do_layout()


def sync_progress_bar(fill, current: int, total: int) -> None:
    track = fill.parent
    if track is None:
        return
    if total <= 0:
        reset_progress_bar(fill)
        return

    ratio = min(1.0, max(0.0, current / total))
    fill.size_hint_x = None
    track_width = track.width
    if track_width > 0:
        fill.width = track_width * ratio
        track.do_layout()
        return

    fill.size_hint_x = ratio
    track.do_layout()
    Clock.schedule_once(lambda _dt, f=fill, r=ratio: _finish_progress_bar_width(f, r), 0)


def _finish_progress_bar_width(fill, ratio: float) -> None:
    track = fill.parent
    if track is None or track.width <= 0:
        return
    fill.size_hint_x = None
    fill.width = track.width * ratio
    track.do_layout()


def _label_text_width(label) -> float:
    """Measure label width with CoreLabel so fonts are resolved reliably."""
    text = label.text or ""
    if not text:
        return dp(1)

    from kivy.core.text import Label as CoreLabel

    font_size = label.font_size or dp(10)
    core = CoreLabel(
        text=text,
        font_size=font_size,
        font_name=label.font_name or "Roboto",
        bold=bool(getattr(label, "bold", False)),
    )
    core.refresh()
    measured = core.texture.size[0]
    estimated = len(text) * font_size * 0.62
    return max(measured, estimated)


def sync_icon_title_row(
    label,
    row,
    anchor,
    icon_box,
    *,
    max_text_width: float,
    title_block_height: float | None = None,
) -> None:
    if not label or not row or not anchor:
        return

    max_w = max(max_text_width, dp(80))
    block_h = title_block_height or dp(14)

    natural_w = _label_text_width(label) + TITLE_WIDTH_SLACK
    use_w = natural_w if natural_w <= max_w else max_w

    if title_block_height:
        label.width = use_w
        label.height = block_h
        label.text_size = (use_w, block_h)
        label.texture_update()
    else:
        single_line_h = max(getattr(label, "font_size", dp(10)) * 1.35, dp(12))
        for _ in range(4):
            label.width = use_w
            label.text_size = (use_w, None)
            label.texture_update()
            if label.texture_size[1] <= single_line_h:
                break
            use_w = min(use_w + dp(4), max_w)
            if use_w >= max_w:
                break

    row.width = ICON_TITLE_ICON_BLOCK + use_w
    row.height = block_h if title_block_height else max(label.texture_size[1], dp(14))
    anchor.height = row.height
    if icon_box is not None:
        icon_box.height = row.height
    row.do_layout()
    anchor.do_layout()


def relayout_feature_cards(root, *, delays: tuple[float, ...] = (0, 0.12, 0.35)) -> None:
    cards = [
        widget
        for widget in root.walk()
        if type(widget).__name__ == "FuturaFeatureCard"
    ]
    for card in cards:
        card.invalidate_title_layout()
        card._schedule_title_layout()
    for delay in delays:
        for card in cards:
            Clock.schedule_once(card._refresh_title_layout, delay)


class IconTitleLayoutMixin:
    title_horizontal_inset = NumericProperty(dp(46))
    title_block_height = NumericProperty(0)

    def invalidate_title_layout(self) -> None:
        self._title_layout_stamp = None

    def _title_layout_key(self) -> tuple[float, str]:
        label = self.ids.get("title_label")
        title = label.text if label else ""
        return (round(self.width, 1), title)

    def _sync_title_layout(self):
        if self.width <= 0:
            return

        layout_key = self._title_layout_key()
        label = self.ids.get("title_label")
        if layout_key == getattr(self, "_title_layout_stamp", None):
            if label and self._title_fits(label):
                return

        block_h = self.title_block_height if self.title_block_height > 0 else None
        sync_icon_title_row(
            label,
            self.ids.get("title_row"),
            self.ids.get("title_anchor"),
            self.ids.get("title_icon_box"),
            max_text_width=self.width - self.title_horizontal_inset,
            title_block_height=block_h,
        )
        self._title_layout_stamp = layout_key
        if label and not self._title_fits(label):
            self._schedule_title_layout_retry()

    def _title_fits(self, label) -> bool:
        if not label.text:
            return True
        min_width = len(label.text) * (label.font_size or dp(10)) * 0.45
        return label.width >= min_width

    def _schedule_title_layout_retry(self) -> None:
        if getattr(self, "_title_layout_retry_scheduled", False):
            return
        self._title_layout_retry_scheduled = True
        Clock.schedule_once(self._retry_title_layout, 0.15)

    def _retry_title_layout(self, _dt):
        self._title_layout_retry_scheduled = False
        self.invalidate_title_layout()
        self._sync_title_layout()

    def _schedule_title_layout(self):
        if getattr(self, "_title_layout_scheduled", False):
            return
        self._title_layout_scheduled = True
        Clock.schedule_once(self._run_title_layout, 0)

    def _run_title_layout(self, _dt):
        self._title_layout_scheduled = False
        self._sync_title_layout()

    def _refresh_title_layout(self, _dt):
        self.invalidate_title_layout()
        self._sync_title_layout()

    def on_size(self, *_args):
        self._schedule_title_layout()


class HoverHighlightMixin:
    hovered = BooleanProperty(False)
    highlight = NumericProperty(0.0)

    def __init__(self, **kwargs):
        self._highlight_target = 0.0
        self._highlight_tick_ev = None
        super().__init__(**kwargs)

    def on_hovered(self, *_args):
        self._stop_highlight_tick()
        target = 1.0 if self.hovered else 0.0
        self._highlight_target = target
        self.highlight = target
        self.sync_appearance()

    def _stop_highlight_tick(self) -> None:
        if self._highlight_tick_ev is not None:
            self._highlight_tick_ev.cancel()
            self._highlight_tick_ev = None

    def _detach_hover(self) -> None:
        self._stop_highlight_tick()
        self.hovered = False
        self.highlight = 0.0
        self._highlight_target = 0.0
        if hasattr(self, "sync_appearance"):
            self.sync_appearance()


_hover_listener_active = False
_hover_clock_event = None
_last_mouse_pos = [0.0, 0.0]


def _current_screen():
    app = MDApp.get_running_app()
    if not app or not app.root:
        return None
    manager = app.root.ids.get("screen_manager")
    if not manager:
        return None
    return manager.current_screen


def _collides_pointer(widget, pos) -> bool:
    if widget.opacity <= 0 or widget.width <= 0 or widget.height <= 0:
        return False
    if getattr(widget, "disabled", False):
        return False

    parent = widget.parent
    if parent is None:
        return False

    wx, wy = pos
    try:
        px, py = parent.to_widget(wx, wy)
    except Exception:
        return False
    return widget.collide_point(px, py)


def _draw_order(widget) -> int:
    parent = widget.parent
    if parent is not None and widget in parent.children:
        return parent.children.index(widget)
    return 0


def _pick_hover_target(widgets, pos):
    hits = [widget for widget in widgets if _collides_pointer(widget, pos)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    def _metric(widget):
        try:
            cx, cy = widget.to_window(widget.center_x, widget.center_y)
            dx = pos[0] - cx
            dy = pos[1] - cy
            dist = dx * dx + dy * dy
        except Exception:
            dist = float("inf")
        return (dist, widget.width * widget.height, _draw_order(widget))

    return min(hits, key=_metric)


def _set_group_hover(widgets, active) -> None:
    for widget in widgets:
        desired = widget is active
        if desired != widget.hovered:
            widget.hovered = desired


def _home_screen_active(app) -> bool:
    if not app or not app.root:
        return False
    manager = app.root.ids.get("screen_manager")
    return bool(manager and manager.current == "home")


def clear_feature_card_hover(root) -> None:
    for widget in root.walk():
        if type(widget).__name__ != "FuturaFeatureCard":
            continue
        if widget.hovered or widget.highlight > 0.001 or widget.pressed:
            widget.pressed = False
            widget._detach_hover()
            widget.sync_appearance()


def clear_option_button_hover(root) -> None:
    for widget in root.walk():
        if not isinstance(widget, (SettingsOptionButton, DvpActionButton)):
            continue
        if widget.hovered or widget.highlight > 0.001:
            widget._detach_hover()
            widget.sync_appearance()


def _update_hover_targets(pos) -> None:
    app = MDApp.get_running_app()
    if not app or not app.root:
        return

    _last_mouse_pos[0] = pos[0]
    _last_mouse_pos[1] = pos[1]

    root = app.root
    home_active = _home_screen_active(app)
    screen = _current_screen()

    cards = []
    option_buttons = []
    if screen is not None:
        for widget in screen.walk():
            if isinstance(widget, FuturaFeatureCard):
                cards.append(widget)
            elif isinstance(widget, (SettingsOptionButton, DvpActionButton)):
                option_buttons.append(widget)

    hit_cards = [card for card in cards if _collides_pointer(card, pos)]
    active_card = _pick_hover_target(hit_cards, pos) if home_active else None

    hit_options = [btn for btn in option_buttons if _collides_pointer(btn, pos)]
    active_option = _pick_hover_target(hit_options, pos)

    for card in cards:
        desired = card is active_card
        if desired != card.hovered:
            card.hovered = desired

    nav_panel = root.ids.get("nav_panel")
    nav_buttons = []
    if nav_panel is not None:
        nav_buttons = [
            child for child in nav_panel.children if isinstance(child, FuturaNavButton)
        ]
    active_nav = _pick_hover_target(nav_buttons, pos)
    _set_group_hover(nav_buttons, active_nav)

    _set_group_hover(option_buttons, active_option)


def _on_global_mouse_pos(_window, pos):
    _update_hover_targets(pos)


def _on_hover_tick(_dt):
    _update_hover_targets(tuple(_last_mouse_pos))


def ensure_hover_listener() -> None:
    global _hover_listener_active, _hover_clock_event
    if _hover_listener_active:
        return
    _hover_listener_active = True
    _last_mouse_pos[0], _last_mouse_pos[1] = Window.mouse_pos
    Window.bind(mouse_pos=_on_global_mouse_pos)
    _hover_clock_event = Clock.schedule_interval(_on_hover_tick, 0)


def _hover_widget_attached() -> None:
    ensure_hover_listener()


def _hover_widget_detached() -> None:
    return


class StatusDot(Widget):
    alpha = NumericProperty(1.0)
    _pulse = None

    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(8), dp(8)), **kwargs)
        with self.canvas:
            self._color = Color(rgba=(0.2, 0.95, 0.55, 1))
            self._ellipse = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_canvas, size=self._sync_canvas, alpha=self._sync_alpha)

    def _sync_alpha(self, *_):
        self._color.rgba = (0.2, 0.95, 0.55, self.alpha)

    def _sync_canvas(self, *_):
        self._ellipse.pos = self.pos
        self._ellipse.size = self.size

    def on_parent(self, _widget, parent):
        if parent is not None:
            if self._pulse is None:
                self._pulse = (
                    Animation(alpha=0.2, duration=1.4, t="in_out_sine")
                    + Animation(alpha=1.0, duration=1.4, t="in_out_sine")
                )
                self._pulse.repeat = True
            self._pulse.start(self)
        elif self._pulse is not None:
            self._pulse.cancel(self)
            self.alpha = 1.0


class TitleBarButton(ButtonBehavior, MDBoxLayout):
    icon = StringProperty("minus")
    action = StringProperty("")

    def on_state(self, *_args):
        self.sync_appearance()

    def on_parent(self, _widget, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return

        self.md_bg_color = (
            palette["accent_glow"] if self.state == "down" else (0, 0, 0, 0)
        )
        for child in self.walk():
            if type(child).__name__ == "MDIcon":
                child.icon_color = palette["accent"]

    def on_release(self):
        if win_chrome.is_chrome_animating():
            return
        handlers = {
            "minimize": win_chrome.minimize,
            "close": win_chrome.close,
        }
        handler = handlers.get(self.action)
        if handler:
            handler()


class ThemeToggleButton(ButtonBehavior, MDBoxLayout):
    theme_icon = StringProperty("weather-sunny")

    def on_parent(self, _widget, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self._sync_icon(), 0)
            self.md_bg_color = (0, 0, 0, 0)

    def on_state(self, *_args):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        glow = palette["accent_glow"] if palette else (0, 0.941, 1, 0.08)
        self.md_bg_color = glow if self.state == "down" else (0, 0, 0, 0)

    def on_release(self):
        if win_chrome.is_chrome_animating() or is_theme_animating():
            return
        toggle_theme()
        self._sync_icon()

    def _sync_icon(self):
        app = MDApp.get_running_app()
        if not app:
            return
        is_dark = app.config.app_global.theme == "dark"
        self.theme_icon = "weather-sunny" if is_dark else "weather-night"


class PassThroughLabel(MDLabel):
    """Label that never intercepts touch/hover hit-testing on parent buttons."""

    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False


class PassThroughHint(PassThroughLabel):
    """Multiline hint text that never blocks pointer interaction."""

    def on_size(self, *_args):
        if self.width > 0:
            self.text_size = (self.width, None)
            self.texture_update()


class SettingsOptionButton(ButtonBehavior, HoverHighlightMixin, MDBoxLayout):
    option_value = StringProperty("")
    option_label = StringProperty("")
    active = BooleanProperty(False)

    def on_active(self, *_args):
        self.sync_appearance()

    def on_state(self, *_args):
        self.sync_appearance()

    def on_parent(self, _widget, parent):
        if parent is not None:
            _hover_widget_attached()
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
        else:
            _hover_widget_detached()
            self._detach_hover()

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return False
        return ButtonBehavior.on_touch_down(self, touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return ButtonBehavior.on_touch_move(self, touch)
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            return ButtonBehavior.on_touch_up(self, touch)
        return False

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return

        surface = palette["surface"]
        glow = palette["accent_glow"]
        accent = palette["accent"]
        accent_dim = palette["accent_dim"]

        if self.active:
            mix = self.highlight
            if self.state == "down":
                mix = min(1.0, mix + 0.55)
            self.md_bg_color = lerp_color(glow, accent, mix * 0.35)
            self.line_color = lerp_color(accent, (1, 1, 1, 1), mix * 0.25)
        else:
            mix = self.highlight
            if self.state == "down":
                mix = min(1.0, mix + 0.55)
            self.md_bg_color = lerp_color(surface, glow, mix * 0.55)
            self.line_color = lerp_color(accent_dim, accent, mix)

        self._sync_option_label_color()
        self.canvas.ask_update()

    def _sync_option_label_color(self):
        app = MDApp.get_running_app()
        if not app or not getattr(app, "palette", None):
            return
        palette = app.palette
        for child in self.children:
            if isinstance(child, MDLabel):
                if self.active:
                    child.text_color = palette["accent"]
                else:
                    child.text_color = lerp_color(
                        palette["muted"], palette["accent"], self.highlight
                    )


class DvpActionButton(ButtonBehavior, HoverHighlightMixin, MDBoxLayout):
    action_label = StringProperty("")

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return False
        return ButtonBehavior.on_touch_down(self, touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return ButtonBehavior.on_touch_move(self, touch)
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            return ButtonBehavior.on_touch_up(self, touch)
        return False

    def on_parent(self, _widget, parent):
        if parent is not None:
            _hover_widget_attached()
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
        else:
            _hover_widget_detached()
            self._detach_hover()

    def on_state(self, *_args):
        self.sync_appearance()

    def on_disabled(self, *_args):
        self.sync_appearance()

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return

        surface = palette["surface"]
        glow = palette["accent_glow"]
        accent = palette["accent"]
        accent_dim = palette["accent_dim"]

        if self.disabled:
            self.md_bg_color = surface
            self.line_color = accent_dim
            label_color = palette["muted"]
        else:
            mix = self.highlight
            if self.state == "down":
                mix = min(1.0, mix + 0.55)
            self.md_bg_color = lerp_color(surface, glow, mix * 0.55)
            self.line_color = lerp_color(accent_dim, accent, mix)
            label_color = lerp_color(palette["muted"], palette["accent"], mix)

        for child in self.children:
            if isinstance(child, MDLabel):
                child.text_color = label_color


class CustomTitleBar(MDBoxLayout):
    def on_parent(self, _widget, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self._sync_theme_button(), 0)

    def _sync_theme_button(self):
        for child in self.walk():
            if isinstance(child, ThemeToggleButton):
                child._sync_icon()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if super().on_touch_down(touch):
                return True
            if not win_chrome.is_chrome_animating():
                win_chrome.drag_window()
            return True
        return super().on_touch_down(touch)


class FuturaNavButton(ButtonBehavior, HoverHighlightMixin, MDBoxLayout):
    icon = StringProperty("circle")
    active = BooleanProperty(False)
    screen_name = StringProperty("home")

    def on_parent(self, _widget, parent):
        if parent is not None:
            _hover_widget_attached()
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
        else:
            _hover_widget_detached()
            self._detach_hover()

    def on_active(self, *_args):
        self.sync_appearance()

    def on_state(self, *_args):
        self.sync_appearance()

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return

        glow = palette["accent_glow"]
        accent = palette["accent"]
        mix = self.highlight
        if self.state == "down":
            mix = min(1.0, mix + 0.55)

        if self.active:
            self.md_bg_color = lerp_color(glow, accent, mix * 0.35)
        else:
            self.md_bg_color = lerp_color((0, 0, 0, 0), glow, mix)

        self.canvas.ask_update()

    def on_release(self):
        navigate_to(self.screen_name)


class FuturaFeatureCard(HoverHighlightMixin, MDCard, IconTitleLayoutMixin):
    card_icon = StringProperty("circle")
    card_title = StringProperty("")
    card_body = StringProperty("")
    screen_name = StringProperty("")
    pressed = BooleanProperty(False)
    title_horizontal_inset = NumericProperty(dp(46))
    title_block_height = NumericProperty(CARD_TITLE_BLOCK_HEIGHT)

    def on_enter(self, *_args):
        self.state_layer_color = [0, 0, 0, 0]

    def on_leave(self, *_args):
        self._state = 0.0
        self.state_layer_color = [0, 0, 0, 0]
        self.sync_appearance()

    def set_properties_widget(self):
        self.state_layer_color = [0, 0, 0, 0]

    def _apply_card_colors(self, bg, border) -> None:
        Animation.cancel_all(self, "_md_bg_color")
        self._bg_color = bg
        self.md_bg_color = bg
        self._md_bg_color = bg
        self.line_color = border
        for instr in self.canvas.get_group("backgroundcolor-behavior-bg-color"):
            instr.rgba = bg
        self.canvas.ask_update()

    def on_card_title(self, *_args):
        self.invalidate_title_layout()
        self._schedule_title_layout()
        Clock.schedule_once(self._refresh_title_layout, 0.12)

    def on_size(self, *_args):
        self._schedule_title_layout()

    def on_parent(self, _widget, parent):
        if parent is not None:
            _hover_widget_attached()
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
            self._schedule_title_layout()
            Clock.schedule_once(self._refresh_title_layout, 0.08)
        else:
            _hover_widget_detached()
            self._detach_hover()

    def on_pressed(self, *_args):
        self.sync_appearance()

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return

        base = tuple(palette["surface"])
        glow = tuple(palette["accent_glow"])
        accent = tuple(palette["accent"])
        accent_dim = tuple(palette["accent_dim"])
        hover_bg = lerp_color(base, glow, 0.55)

        mix = self.highlight
        if self.pressed:
            mix = min(1.0, mix + 0.45)

        bg = lerp_color(base, hover_bg, mix)
        border = lerp_color(accent_dim, accent, mix)
        self._apply_card_colors(bg, border)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.pressed = True
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            was_pressed = self.pressed
            self.pressed = False
            if was_pressed and self.collide_point(*touch.pos) and self.screen_name:
                navigate_to(self.screen_name)
            return True
        return super().on_touch_up(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.pressed and not self.collide_point(*touch.pos):
                self.pressed = False
            return True
        return super().on_touch_move(touch)


class PlaceholderPane(IconTitleLayoutMixin, MDBoxLayout):
    module_icon = StringProperty("hammer-wrench")
    pane_title = StringProperty("")
    pane_subtitle = StringProperty("")
    title_horizontal_inset = NumericProperty(dp(74))

    def on_pane_title(self, *_args):
        self.invalidate_title_layout()
        self._schedule_title_layout()

    def on_parent(self, _widget, parent):
        if parent is not None:
            self._schedule_title_layout()
            Clock.schedule_once(self._refresh_title_layout, 0.08)


NOTICE_STYLE = {
    "dark": {
        "bg": (0.36, 0.06, 0.08, 1),
        "border": (0.92, 0.22, 0.26, 0.55),
        "icon": (1, 0.42, 0.42, 1),
        "text": (0.96, 0.86, 0.86, 1),
        "dismiss": (0.82, 0.55, 0.55, 1),
        "dismiss_glow": (0.92, 0.22, 0.26, 0.18),
    },
    "light": {
        "bg": (0.94, 0.78, 0.78, 1),
        "border": (0.72, 0.12, 0.16, 0.55),
        "icon": (0.72, 0.08, 0.12, 1),
        "text": (0.22, 0.02, 0.04, 1),
        "dismiss": (0.52, 0.12, 0.14, 1),
        "dismiss_glow": (0.72, 0.12, 0.16, 0.2),
    },
}


def _find_admin_notice_bar(widget):
    seen: set[int] = set()
    bar = widget
    depth = 0
    while bar is not None and id(bar) not in seen and depth < 32:
        if isinstance(bar, AdminNoticeBar):
            return bar
        seen.add(id(bar))
        bar = bar.parent
        depth += 1
    return None


def _apply_notice_icon_color(icon, color) -> None:
    icon.theme_icon_color = "Custom"
    icon.icon_color = color
    icon.color = color


class AdminNoticeDismissButton(ButtonBehavior, MDBoxLayout):
    dismiss_icon_color = ListProperty([0.82, 0.55, 0.55, 1])

    def on_state(self, *_args):
        self.sync_appearance()

    def on_parent(self, _widget, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)

    def on_release(self):
        bar = _find_admin_notice_bar(self)
        if bar is not None:
            bar.dismiss()

    def sync_appearance(self, style: dict | None = None):
        if style is None:
            bar = _find_admin_notice_bar(self.parent)
            if bar is not None:
                style = bar.notice_style
        if not style:
            return

        self.md_bg_color = (
            style["dismiss_glow"] if self.state == "down" else (0, 0, 0, 0)
        )
        self.dismiss_icon_color = style["dismiss"]
        for child in self.walk():
            if is_icon_widget(child):
                _apply_notice_icon_color(child, style["dismiss"])


class AdminNoticeBar(MDBoxLayout):
    visible = BooleanProperty(False)
    message = StringProperty("")
    notice_bg_color = ListProperty([0.36, 0.06, 0.08, 1])
    notice_border_color = ListProperty([0.92, 0.22, 0.26, 0.55])
    notice_icon_color = ListProperty([1, 0.42, 0.42, 1])
    notice_text_color = ListProperty([0.96, 0.86, 0.86, 1])
    notice_style = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        self._visible_initialized = False
        super().__init__(**kwargs)

    def show(self, message: str):
        self.message = message
        if self.visible:
            self.sync_appearance()
            return
        self.visible = True
        self.opacity = 1
        self.height = dp(44)
        self.disabled = False
        self.sync_appearance()
        self._schedule_appearance_resync()
        self._schedule_layout_refresh()

    def dismiss(self):
        if not self.visible:
            return
        self.visible = False
        self.opacity = 0
        self.height = 0
        self.disabled = True
        self._schedule_layout_refresh()

    def on_visible(self, instance, value):
        if not self._visible_initialized:
            self._visible_initialized = True
            self.opacity = 0
            self.height = 0
            return
        self.disabled = not value
        if value:
            self.sync_appearance()
            self._schedule_appearance_resync()

    def _schedule_appearance_resync(self):
        Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
        Clock.schedule_once(lambda _dt: self.sync_appearance(), 0.05)
        Clock.schedule_once(lambda _dt: self.sync_appearance(), 0.12)

    def _schedule_layout_refresh(self):
        app = MDApp.get_running_app()
        if not app or not app.root:
            return

        from utils.screen_layout import prepare_screens

        root = app.root

        def _after_layout(_dt):
            prepare_screens(root)
            if self.visible:
                self.sync_appearance()

        Clock.schedule_once(_after_layout, 0)

    def on_parent(self, _widget, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)

    def sync_appearance(self):
        app = MDApp.get_running_app()
        if not app:
            return

        theme = app.config.app_global.theme
        style = NOTICE_STYLE.get(theme, NOTICE_STYLE["dark"])
        self.notice_style = style
        self.notice_bg_color = style["bg"]
        self.notice_border_color = style["border"]
        self.notice_icon_color = style["icon"]
        self.notice_text_color = style["text"]
        self.md_bg_color = style["bg"]

        for child in self.walk():
            if is_icon_widget(child):
                if getattr(child, "icon", "") == "close":
                    _apply_notice_icon_color(child, style["dismiss"])
                else:
                    _apply_notice_icon_color(child, style["icon"])
            elif isinstance(child, MDLabel):
                child.text_color = style["text"]
                child.color = style["text"]
            elif isinstance(child, AdminNoticeDismissButton):
                child.sync_appearance(style)
