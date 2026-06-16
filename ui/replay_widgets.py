from io import BytesIO

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout

from lib.replay_parser.avatar_frames import frame_color_for_kind
from utils.avatar_loader import load_avatar
from utils.tank_marks_image import render_tank_marks_png


class TankMarksIndicator(Image):
    marks_count = NumericProperty(0)

    _STRIPE_WIDTH = dp(5)
    _STRIPE_GAP = dp(0)
    _STRIPE_OVERLAP = dp(2)
    _STRIPE_HEIGHT = dp(11)
    _VERTICAL_LIFT = dp(2)

    @staticmethod
    def width_for_count(count: int) -> float:
        if count <= 0:
            return 0
        stripe = dp(5)
        gap = dp(0)
        overlap = dp(2)
        step = stripe - overlap
        return stripe + max(0, int(count) - 1) * (step + gap)

    @staticmethod
    def mark_height() -> float:
        return dp(11)

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_x", None)
        kwargs.setdefault("size_hint_y", 1)
        kwargs.setdefault("fit_mode", "contain")
        super().__init__(**kwargs)
        self.bind(marks_count=self._rebuild_marks, size=self._sync_layout, parent=self._on_parent)
        Clock.schedule_once(lambda _dt: self._rebuild_marks(), 0)

    def _on_parent(self, _instance, parent):
        if parent is not None:
            Clock.schedule_once(lambda _dt: self._rebuild_marks(), 0)

    def _pixel_metrics(self) -> tuple[int, int, int, int, int]:
        return (
            max(1, int(round(self._STRIPE_WIDTH))),
            max(1, int(round(self._STRIPE_HEIGHT))),
            max(0, int(round(self._STRIPE_GAP))),
            max(0, int(round(self._STRIPE_OVERLAP))),
            max(0, int(round(self._VERTICAL_LIFT))),
        )

    def _rebuild_marks(self, *_args):
        count = int(self.marks_count)
        if count <= 0:
            self.width = 0
            self.texture = None
            return

        stripe_width, stripe_height, gap, overlap, vertical_lift = self._pixel_metrics()
        png = render_tank_marks_png(
            count,
            stripe_width=stripe_width,
            stripe_height=stripe_height,
            gap=gap,
            overlap=overlap,
            vertical_lift=vertical_lift,
        )
        self.texture = CoreImage(BytesIO(png), ext="png").texture
        self._sync_layout()

    def _sync_layout(self, *_args):
        count = int(self.marks_count)
        if count <= 0 or self.texture is None:
            return
        self.width = self.width_for_count(count)

    _sync_text_size = _sync_layout
    _sync_marks = _rebuild_marks


def sync_inline_marks(
    label,
    marks,
    *,
    marks_count: int,
    max_width: float | None = None,
    gap: float = 0,
    label_height: float | None = None,
) -> float:
    count = int(marks_count)
    marks.marks_count = count
    marks_width = TankMarksIndicator.width_for_count(count)
    spacing = gap if count else 0

    label.text_size = (None, None)
    label.texture_update()
    natural_width = label.texture_size[0]
    if max_width is not None:
        text_budget = max(dp(8), max_width - marks_width - spacing)
        natural_width = min(natural_width, text_budget)

    label.width = natural_width
    label.size_hint_x = None
    if label_height is None:
        label.text_size = (natural_width, None)
    else:
        label.text_size = (natural_width, label_height)
    label.texture_update()
    marks._rebuild_marks()
    Clock.schedule_once(lambda _dt: marks._sync_layout(), 0)
    return natural_width + (marks_width + spacing if count else 0)


class ReplayTankCell(MDBoxLayout):
    tank_label = StringProperty("")
    marks_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._syncing = False
        self.bind(tank_label=self._request_sync, marks_count=self._request_sync, width=self._request_sync)

    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda _dt: self._request_sync(), 0)

    def _request_sync(self, *_args):
        if self._syncing or self.width <= 0:
            return
        self._sync_layout()
        if self.marks_count:
            Clock.schedule_once(lambda _dt: self._sync_layout(), 0)

    def _sync_layout(self):
        group = self.ids.get("tank_group")
        label = self.ids.get("tank_name")
        marks = self.ids.get("tank_marks")
        if group is None or label is None or marks is None or self.width <= 0:
            return

        self._syncing = True
        try:
            marks_count = int(self.marks_count)
            group.width = sync_inline_marks(
                label,
                marks,
                marks_count=marks_count,
                gap=group.spacing,
            )
            group.size_hint_x = None
            Clock.schedule_once(lambda _dt: marks._sync_text_size(), 0)
        finally:
            self._syncing = False


class ReplayAvatar(Widget):
    avatar_url = StringProperty("")
    frame_kind = StringProperty("")

    _FRAME_WIDTH = dp(1)
    _IMAGE_INSET = dp(2)

    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(21), dp(21)), **kwargs)
        self._image: Image | None = None
        self._frame_color = Color(rgba=(0.5, 0.5, 0.5, 1))
        self._frame = Ellipse(pos=self.pos, size=self.size)
        with self.canvas.before:
            self._frame_color
            self._frame
        self.bind(
            avatar_url=self._reload_avatar,
            frame_kind=self._sync_frame,
            pos=self._sync_geometry,
            size=self._sync_geometry,
        )
        Clock.schedule_once(lambda _dt: self._reload_avatar(), 0)

    def _reload_avatar(self, *_args):
        if self._image is None:
            self._image = Image(fit_mode="cover", size_hint=(None, None))
            self.add_widget(self._image)
        if not self.avatar_url:
            self._image.source = ""
            self._sync_geometry()
            return
        load_avatar(self.avatar_url, self._on_avatar_loaded)

    def _on_avatar_loaded(self, path: str | None) -> None:
        if self._image is None:
            return
        self._image.source = path or ""
        self._sync_geometry()

    def _sync_frame(self, *_args):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if palette is None:
            return
        self._frame_color.rgba = frame_color_for_kind(self.frame_kind, palette)

    def _sync_geometry(self, *_args):
        self._frame.pos = self.pos
        self._frame.size = self.size
        if self._image is None:
            return
        inset = self._IMAGE_INSET
        self._image.pos = (self.x + inset, self.y + inset)
        self._image.size = (self.width - inset * 2, self.height - inset * 2)


class ReplayPlayerRow(MDBoxLayout):
    nickname = StringProperty("")
    clan_tag = StringProperty("")
    tank_label = StringProperty("")
    damage_text = StringProperty("0")
    kills_text = StringProperty("0")
    xp_text = StringProperty("0")
    credits_text = StringProperty("0")
    avatar_url = StringProperty("")
    frame_kind = StringProperty("")
    marks_count = NumericProperty(0)
    row_index = NumericProperty(0)

    def apply_row(self, row, *, row_index: int = 0) -> None:
        self.row_index = row_index
        self.nickname = row.nickname
        self.clan_tag = f"[{row.clan_tag}]" if row.clan_tag else ""
        self.tank_label = row.tank_label
        self.damage_text = str(row.damage)
        self.kills_text = str(row.kills)
        self.xp_text = str(row.xp)
        self.credits_text = str(row.credits)
        self.avatar_url = row.avatar_url
        self.frame_kind = row.frame_kind
        self.marks_count = int(row.marks or 0)
        self.sync_appearance()

    def sync_appearance(self):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return
        if self.row_index % 2 == 0:
            self.md_bg_color = palette["bg_panel"]
        else:
            self.md_bg_color = palette["surface"]
        avatar = self.ids.get("avatar")
        if avatar is not None:
            avatar.frame_kind = self.frame_kind
            avatar.avatar_url = self.avatar_url
        tank_cell = self.ids.get("tank_cell")
        if tank_cell is not None:
            tank_cell.tank_label = self.tank_label
            tank_cell.marks_count = self.marks_count
            Clock.schedule_once(lambda _dt: tank_cell._request_sync(), 0)


class TopAlignedHBox(MDBoxLayout):
    """Horizontal row that keeps children aligned to the top edge."""

    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        super().__init__(**kwargs)

    def do_layout(self, *args):
        super().do_layout(*args)
        row_top = self.y + self.height
        for child in self.children:
            child.y = row_top - child.height


class ReplayTeamPanel(MDBoxLayout):
    team_title = StringProperty("")
    team_badge = StringProperty("")
    badge_is_win = BooleanProperty(False)
    badge_color = ListProperty([0.5, 0.5, 0.5, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(badge_is_win=self._sync_badge_color)

    def on_kv_post(self, base_widget):
        self._sync_badge_color()
        app = MDApp.get_running_app()
        if app is not None:
            code = app.config.app_global.language
            if code not in app.locales.data:
                code = "ru"
            self.refresh_columns(app.locales.data[code].main.replay.columns)

    def refresh_columns(self, columns) -> None:
        mapping = {
            "col_player": columns.player,
            "col_tank": columns.tank,
            "col_damage": columns.damage,
            "col_kills": columns.kills,
            "col_xp": columns.xp,
            "col_credits": columns.credits,
        }
        for col_id, text in mapping.items():
            label = self.ids.get(col_id)
            if label is not None:
                label.text = text

    def _sync_badge_color(self, *_args):
        app = MDApp.get_running_app()
        palette = getattr(app, "palette", None) if app else None
        if not palette:
            return
        if self.badge_is_win:
            self.badge_color = list(palette["success"])
        elif self.team_badge:
            self.badge_color = list(palette["danger"])
        else:
            self.badge_color = list(palette["muted"])

    def set_players(
        self,
        rows,
        *,
        is_winner: bool,
        is_loser: bool,
        win_label: str,
        lose_label: str,
    ) -> None:
        if is_winner:
            self.team_badge = win_label
            self.badge_is_win = True
        elif is_loser:
            self.team_badge = lose_label
            self.badge_is_win = False
        else:
            self.team_badge = ""
            self.badge_is_win = False
        self._sync_badge_color()

        container = self.ids.rows_box
        container.clear_widgets()
        for index, row in enumerate(rows):
            item = ReplayPlayerRow()
            item.apply_row(row, row_index=index)
            container.add_widget(item)
