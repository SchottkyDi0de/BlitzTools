from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
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


def sync_icon_title_row(label, row, anchor, icon_box, *, max_text_width: float) -> None:
    if not label or not row or not anchor:
        return

    max_w = max(max_text_width, dp(80))

    label.text_size = (None, None)
    label.texture_update()
    natural_w = max(label.texture_size[0], dp(1))

    if natural_w <= max_w:
        label.width = natural_w
        label.text_size = (natural_w, None)
        row.width = ICON_TITLE_ICON_BLOCK + natural_w
    else:
        label.width = max_w
        label.text_size = (max_w, None)
        row.width = ICON_TITLE_ICON_BLOCK + max_w

    label.texture_update()
    row.height = max(label.texture_size[1], dp(14))
    anchor.height = row.height
    if icon_box is not None:
        icon_box.height = row.height
    row.do_layout()
    anchor.do_layout()


class IconTitleLayoutMixin:
    title_horizontal_inset = NumericProperty(dp(46))

    def _sync_title_layout(self):
        sync_icon_title_row(
            self.ids.get("title_label"),
            self.ids.get("title_row"),
            self.ids.get("title_anchor"),
            self.ids.get("title_icon_box"),
            max_text_width=self.width - self.title_horizontal_inset,
        )

    def _schedule_title_layout(self):
        Clock.schedule_once(lambda _dt: self._sync_title_layout(), 0)

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
        self._set_highlight_target(1.0 if self.hovered else 0.0)

    def _set_highlight_target(self, target: float) -> None:
        self._highlight_target = target
        if self._highlight_tick_ev is None:
            self._highlight_tick_ev = Clock.schedule_interval(self._tick_highlight, 0)

    def _tick_highlight(self, dt: float) -> None:
        target = self._highlight_target
        diff = target - self.highlight
        if abs(diff) < 0.001:
            if self.highlight != target:
                self.highlight = target
                self.sync_appearance()
            self._stop_highlight_tick()
            return

        alpha = 1.0 - pow(0.001, dt / max(HOVER_ANIM_DURATION, 0.001))
        self.highlight += diff * alpha
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


_hover_listener_count = 0
_hover_clock_event = None
_last_mouse_pos = [0.0, 0.0]

_SCROLL_TYPES = frozenset({"ScrollView", "MDScrollView"})


def _pointer_over_widget(widget, pos) -> bool:
    if widget.opacity <= 0 or widget.width <= 0 or widget.height <= 0:
        return False
    if not widget.get_root_window():
        return False

    wx, wy = pos
    try:
        lx, ly = widget.to_widget(wx, wy)
    except Exception:
        return False
    if not widget.collide_point(lx, ly):
        return False

    parent = widget.parent
    seen: set[int] = set()
    depth = 0
    while parent is not None and id(parent) not in seen and depth < 64:
        seen.add(id(parent))
        if type(parent).__name__ in _SCROLL_TYPES:
            sx, sy = parent.to_widget(wx, wy)
            if not parent.collide_point(sx, sy):
                return False
        parent = parent.parent
        depth += 1
    return True


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


def _update_hover_targets(pos) -> None:
    app = MDApp.get_running_app()
    if not app or not app.root:
        return

    _last_mouse_pos[0] = pos[0]
    _last_mouse_pos[1] = pos[1]

    home_active = _home_screen_active(app)

    for widget in app.root.walk():
        if isinstance(widget, FuturaFeatureCard):
            if not home_active:
                if widget.hovered or widget.highlight > 0.001:
                    widget._detach_hover()
                    widget.sync_appearance()
                continue
            inside = _pointer_over_widget(widget, pos)
            if inside != widget.hovered:
                widget.hovered = inside
            continue

        if not isinstance(widget, (FuturaNavButton, SettingsOptionButton)):
            continue
        inside = _pointer_over_widget(widget, pos)
        if inside != widget.hovered:
            widget.hovered = inside


def _on_global_mouse_pos(_window, pos):
    _update_hover_targets(pos)


def _on_hover_tick(_dt):
    _update_hover_targets(tuple(_last_mouse_pos))


def _hover_widget_attached() -> None:
    global _hover_listener_count, _hover_clock_event
    _hover_listener_count += 1
    if _hover_listener_count == 1:
        _last_mouse_pos[0], _last_mouse_pos[1] = Window.mouse_pos
        Window.bind(mouse_pos=_on_global_mouse_pos)
        _hover_clock_event = Clock.schedule_interval(_on_hover_tick, 0)


def _hover_widget_detached() -> None:
    global _hover_listener_count, _hover_clock_event
    _hover_listener_count -= 1
    if _hover_listener_count <= 0:
        _hover_listener_count = 0
        Window.unbind(mouse_pos=_on_global_mouse_pos)
        if _hover_clock_event is not None:
            _hover_clock_event.cancel()
            _hover_clock_event = None


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
            self.md_bg_color = glow
            self.line_color = accent
        else:
            mix = self.highlight
            if self.state == "down":
                mix = min(1.0, mix + 0.55)
            self.md_bg_color = lerp_color(surface, glow, mix * 0.55)
            self.line_color = lerp_color(accent_dim, accent, mix)

        self._sync_option_label_color()

    def _sync_option_label_color(self):
        app = MDApp.get_running_app()
        if not app or not getattr(app, "palette", None):
            return
        palette = app.palette
        for child in self.children:
            if isinstance(child, MDLabel):
                child.text_color = palette["accent"] if self.active else palette["muted"]


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
        if self.active:
            self.md_bg_color = glow
            return

        mix = self.highlight
        if self.state == "down":
            mix = min(1.0, mix + 0.55)

        self.md_bg_color = lerp_color((0, 0, 0, 0), glow, mix)

    def on_release(self):
        navigate_to(self.screen_name)


class FuturaFeatureCard(HoverHighlightMixin, MDCard, IconTitleLayoutMixin):
    card_icon = StringProperty("circle")
    card_title = StringProperty("")
    card_body = StringProperty("")
    screen_name = StringProperty("")
    pressed = BooleanProperty(False)
    title_horizontal_inset = NumericProperty(dp(46))

    def on_card_title(self, *_args):
        self._schedule_title_layout()

    def on_size(self, *_args):
        self._schedule_title_layout()

    def on_parent(self, _widget, parent):
        if parent is not None:
            _hover_widget_attached()
            Clock.schedule_once(lambda _dt: self.sync_appearance(), 0)
            self._schedule_title_layout()
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

        self.md_bg_color = lerp_color(base, hover_bg, mix)
        self.line_color = lerp_color(accent_dim, accent, mix)
        self.canvas.ask_update()

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
        self._schedule_title_layout()

    def on_parent(self, _widget, parent):
        if parent is not None:
            self._schedule_title_layout()
