from __future__ import annotations

from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from lib.config.handler import ConfigHandler
from lib.olenemer.service import get_olenemer_runtime
from utils.file_dialogs import pick_folder

from lib.olenemer.window.columns import FIXED_COLUMNS, HIDDEN_COLUMNS, TOGGLEABLE_COLUMNS


class OlenemerScreen(MDScreen):
    name = "olenemer"

    def on_enter(self, *_args):
        self.refresh_locale()
        self.load_from_config()
        self._sync_launch_ui()

    def refresh_locale(self) -> None:
        loc = self._locale()
        if not loc:
            return

        self.ids.screen_title.text = loc.title
        self.ids.screen_hint.text = loc.description

        sections = loc.sections
        self.ids.launch_section.text = sections.launch
        self.ids.general_section.text = sections.general
        self.ids.regions_section.text = sections.regions
        self.ids.appearance_section.text = sections.appearance
        self.ids.columns_section.text = sections.columns
        self.ids.replay_paths_section.text = sections.replay_paths
        self.ids.keybinds_section.text = sections.keybinds

        self.ids.auto_open_btn.option_label = loc.options.auto_open
        self.ids.profile_skins_btn.option_label = loc.options.profile_skins
        self.ids.region_ru_btn.option_label = loc.regions.ru
        self.ids.region_eu_btn.option_label = loc.regions.eu
        self.ids.show_border_btn.option_label = loc.options.show_border
        self.ids.show_window_border_btn.option_label = loc.options.show_window_border
        self.ids.show_summary_btn.option_label = loc.options.show_summary

        self.ids.bg_transparent_btn.option_label = loc.background.transparent
        self.ids.bg_image_btn.option_label = loc.background.image
        self.ids.tank_icon_btn.option_label = loc.tank_display.icon
        self.ids.tank_color_btn.option_label = loc.tank_display.color

        column_labels = loc.columns
        mapping = {
            "col_rating_btn": column_labels.rating,
            "col_battles_btn": column_labels.battles,
            "col_winrate_btn": column_labels.winrate,
            "col_damage_btn": column_labels.damage,
        }
        for widget_id, label in mapping.items():
            widget = self.ids.get(widget_id)
            if widget is not None:
                widget.option_label = label
                widget.sync_appearance()

        actions = loc.actions
        self.ids.start_btn.action_label = actions.start
        self.ids.stop_btn.action_label = actions.stop
        self.ids.pick_ru_path_btn.action_label = actions.pick_ru_replays
        self.ids.pick_eu_path_btn.action_label = actions.pick_eu_replays
        self.ids.opacity_down_btn.action_label = actions.opacity_down
        self.ids.opacity_up_btn.action_label = actions.opacity_up

        for widget_id in (
            "start_btn",
            "stop_btn",
            "pick_ru_path_btn",
            "pick_eu_path_btn",
            "opacity_down_btn",
            "opacity_up_btn",
        ):
            widget = self.ids.get(widget_id)
            if widget is not None:
                widget.sync_appearance()

        self._sync_keybind_labels(loc)
        self._sync_replay_paths_ui(loc)
        self._sync_transparency_ui(loc)
        self.ids.keybinds_hint.text = loc.keybinds.hint

    def load_from_config(self) -> None:
        app = MDApp.get_running_app()
        if not app:
            return

        olenemer = app.config.olenemer
        self._sync_toggle("auto_open_btn", olenemer.auto_open)
        self._sync_toggle("profile_skins_btn", olenemer.profile_skins)
        self._sync_toggle("region_ru_btn", olenemer.regions.ru)
        self._sync_toggle("region_eu_btn", olenemer.regions.eu)
        self._sync_toggle("show_border_btn", olenemer.show_border)
        self._sync_toggle("show_window_border_btn", olenemer.show_window_border)
        self._sync_toggle("show_summary_btn", olenemer.show_summary)

        for field in TOGGLEABLE_COLUMNS:
            self._sync_toggle(f"col_{field}_btn", getattr(olenemer.column_status, field))

        bg_type = olenemer.background_type
        if bg_type == "color":
            bg_type = "transparent"

        for value, btn_id in (
            ("transparent", "bg_transparent_btn"),
            ("image", "bg_image_btn"),
        ):
            btn = self.ids.get(btn_id)
            if btn is not None:
                btn.active = bg_type == value
                btn.sync_appearance()

        for value, btn_id in (
            ("icon", "tank_icon_btn"),
            ("color", "tank_color_btn"),
        ):
            btn = self.ids.get(btn_id)
            if btn is not None:
                btn.active = olenemer.tank_display_type == value
                btn.sync_appearance()

        loc = self._locale()
        if loc:
            self._sync_keybind_labels(loc)
            self._sync_replay_paths_ui(loc)
            self._sync_transparency_ui(loc)

    def start_olenemer(self) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        if get_olenemer_runtime().start(ConfigHandler()):
            self._sync_launch_ui()

    def stop_olenemer(self) -> None:
        get_olenemer_runtime().stop()
        Clock.schedule_once(lambda _dt: self._sync_launch_ui(), 0.2)

    def toggle_auto_open(self) -> None:
        self._toggle_bool("auto_open")

    def toggle_profile_skins(self) -> None:
        self._toggle_bool("profile_skins")

    def toggle_region_ru(self) -> None:
        self._toggle_region("ru")

    def toggle_region_eu(self) -> None:
        self._toggle_region("eu")

    def toggle_show_border(self) -> None:
        self._toggle_bool("show_border")

    def toggle_show_window_border(self) -> None:
        self._toggle_bool("show_window_border")

    def toggle_show_summary(self) -> None:
        self._toggle_bool("show_summary")

    def toggle_column(self, field: str) -> None:
        app = MDApp.get_running_app()
        if not app or field not in TOGGLEABLE_COLUMNS:
            return
        column_status = app.config.olenemer.column_status
        current = getattr(column_status, field)
        setattr(column_status, field, not current)
        self._write_config(app)
        self._sync_toggle(f"col_{field}_btn", getattr(column_status, field))

    def select_background_type(self, value: str) -> None:
        app = MDApp.get_running_app()
        if not app or value not in {"transparent", "image"}:
            return
        app.config.olenemer.background_type = value
        self._write_config(app)
        self.load_from_config()

    def select_tank_display_type(self, value: str) -> None:
        app = MDApp.get_running_app()
        if not app or value not in {"icon", "color"}:
            return
        app.config.olenemer.tank_display_type = value
        self._write_config(app)
        self.load_from_config()

    def adjust_transparency(self, delta: float) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        current = float(app.config.olenemer.window_transparency)
        opacity = max(0.2, min(1.0, round(current + delta, 2)))
        if opacity == current:
            return
        app.config.olenemer.window_transparency = opacity
        self._write_config(app)
        loc = self._locale()
        if loc:
            self._sync_transparency_ui(loc)

    def pick_replay_path(self, region: str) -> None:
        app = MDApp.get_running_app()
        loc = self._locale()
        if not app or not loc:
            return

        title = (
            loc.actions.pick_ru_replays_dialog
            if region == "ru"
            else loc.actions.pick_eu_replays_dialog
        )
        folder = pick_folder(title=title)
        if not folder:
            return

        if region == "ru":
            app.config.app_global.replay_paths.ru = folder
        else:
            app.config.app_global.replay_paths.eu = folder
        self._write_config(app)
        self._sync_replay_paths_ui(loc)

    def _toggle_bool(self, field: str) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        current = getattr(app.config.olenemer, field)
        setattr(app.config.olenemer, field, not current)
        self._write_config(app)
        self._sync_toggle(f"{field}_btn", not current)

    def _toggle_region(self, region: str) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        regions = app.config.olenemer.regions
        current = getattr(regions, region)
        setattr(regions, region, not current)
        self._write_config(app)
        self._sync_toggle(f"region_{region}_btn", not current)

    def _sync_toggle(self, widget_id: str, active: bool) -> None:
        widget = self.ids.get(widget_id)
        if widget is not None:
            widget.active = active
            widget.sync_appearance()

    def _sync_launch_ui(self) -> None:
        loc = self._locale()
        if not loc:
            return
        running = get_olenemer_runtime().is_running()
        self.ids.start_btn.disabled = running
        self.ids.stop_btn.disabled = not running
        self.ids.start_btn.sync_appearance()
        self.ids.stop_btn.sync_appearance()
        self.ids.launch_status.text = loc.status.running if running else loc.status.idle

    def _sync_transparency_ui(self, loc) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        percent = int(round(float(app.config.olenemer.window_transparency) * 100))
        self.ids.transparency_label.text = loc.options.transparency_value.format(value=percent)

    def _sync_replay_paths_ui(self, loc) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        paths = app.config.app_global.replay_paths
        self.ids.ru_path_label.text = loc.replay_paths.ru_active.format(path=paths.ru)
        self.ids.eu_path_label.text = loc.replay_paths.eu_active.format(path=paths.eu)

    def _sync_keybind_labels(self, loc) -> None:
        app = MDApp.get_running_app()
        if not app:
            return
        keybinds = app.config.olenemer.keybinds
        self.ids.keybind_show_hide_label.text = loc.keybinds.show_hide.format(value=keybinds.show_hide)
        self.ids.keybind_increase_label.text = loc.keybinds.increase_opacity.format(
            value=keybinds.increase_opacity
        )
        self.ids.keybind_decrease_label.text = loc.keybinds.decrease_opacity.format(
            value=keybinds.decrease_opacity
        )

    def _locale(self):
        app = MDApp.get_running_app()
        code = app.config.app_global.language if app else "ru"
        if app and code not in app.locales.data:
            code = "ru"
        return app.locales.data[code].main.olenemer if app else None

    def _write_config(self, app) -> None:
        column_status = app.config.olenemer.column_status
        for field in FIXED_COLUMNS:
            setattr(column_status, field, True)
        for field in HIDDEN_COLUMNS:
            setattr(column_status, field, False)
        handler = ConfigHandler()
        handler.config = app.config
        handler.write_config()
        get_olenemer_runtime().apply_config()
