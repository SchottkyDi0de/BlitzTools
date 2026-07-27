from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from lib.config.handler import ConfigHandler
from lib.olenemer.window.background import background_from_config
from lib.olenemer.window.models import TeamViewData
from lib.olenemer.window.panel import ColumnVisibility
from lib.olenemer.window.service import load_teams_for_replay
from lib.olenemer.window.tcl_env import prepare_olenemer_tk_env
from lib.olenemer.window.team_window import OlenemerWindow
from lib.olenemer.window.theme import accent_color_hex
from utils.app_icon import apply_tk_window_icon


class OlenemerApp(ctk.CTk):
    def __init__(
        self,
        tv_data: dict[int, TeamViewData],
        config_handler: ConfigHandler,
        *,
        region: str,
        live_mode: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title("BlitzTools — Оленемер")
        self.withdraw()
        self.geometry("1x1+-2000+-2000")
        self.after(0, lambda: apply_tk_window_icon(self))
        self.region = region
        self.live_mode = live_mode
        self.config_handler = config_handler
        self.olenemer_config = config_handler.config.olenemer
        self.background = background_from_config(self.olenemer_config)
        self.column_visibility = ColumnVisibility.from_config_for_battle(
            self.olenemer_config.column_status,
            tv_data,
        )
        self.accent_color = accent_color_hex(config_handler.config.app_global.theme)
        self.windows: list[OlenemerWindow] = []

        if not live_mode:
            self.after(0, self._init_windows, tv_data)

    @classmethod
    def for_live(cls, config_handler: ConfigHandler) -> OlenemerApp:
        empty_teams = {
            1: TeamViewData(title="Союзники", rows=[]),
            2: TeamViewData(title="Противники", rows=[]),
        }
        return cls(
            empty_teams,
            config_handler,
            region="ru",
            live_mode=True,
        )

    def _init_windows(self, tv_data: dict[int, TeamViewData]) -> None:
        for team in (1, 2):
            self.add_window(team, tv_data[team])
        self.update_idletasks()
        for window in self.windows:
            if window._last_outer_size is not None:
                window._apply_outer_geometry(*window._last_outer_size)
            window.deiconify()
            window._ensure_topmost()

    def get_window(self, team: int) -> OlenemerWindow | None:
        for window in self.windows:
            if window.team == team:
                return window
        return None

    def save_window_positions(self) -> None:
        left = self.get_window(1)
        right = self.get_window(2)
        if left is not None and left.winfo_exists():
            self.olenemer_config.window_pos_left = [left.winfo_x(), left.winfo_y()]
        if right is not None and right.winfo_exists():
            self.olenemer_config.window_pos_right = [
                right.winfo_x() + right.winfo_width(),
                right.winfo_y(),
            ]
        self.config_handler.write_config()

    def add_window(self, team: int, team_data: TeamViewData) -> OlenemerWindow:
        position = (
            self.olenemer_config.window_pos_left
            if team == 1
            else self.olenemer_config.window_pos_right
        )
        window = OlenemerWindow(
            self,
            team,
            team_data,
            background=self.background,
            position=position,
            columns=self.column_visibility,
            border_color=self.accent_color,
            show_profile_skins=self.olenemer_config.profile_skins,
            tank_display_type=self.olenemer_config.tank_display_type,
            show_window_border=self.olenemer_config.show_window_border,
            show_border=self.olenemer_config.show_border,
            show_summary=self.olenemer_config.show_summary,
        )
        self.windows.append(window)
        return window

    def show_window(self, team: int) -> None:
        window = self.get_window(team)
        if window is not None:
            window.lift()

    def hide_window(self, team: int) -> None:
        window = self.get_window(team)
        if window is not None:
            window.withdraw()

    def update_window(self, team: int, team_data: TeamViewData) -> None:
        window = self.get_window(team)
        if window is not None:
            window.team_data = team_data
            window._team_data = team_data
            window._rerender()

    def update_teams(self, tv_data: dict[int, TeamViewData]) -> None:
        self.column_visibility = ColumnVisibility.from_config_for_battle(
            self.olenemer_config.column_status,
            tv_data,
        )
        for team in (1, 2):
            window = self.get_window(team)
            if window is None:
                self.add_window(team, tv_data[team])
                continue
            window.panel.columns = self.column_visibility
            window.panel.show_profile_skins = self.olenemer_config.profile_skins
            window.panel.tank_display_type = self.olenemer_config.tank_display_type
            window.panel.show_border = self.olenemer_config.show_border
            window.panel.show_summary = self.olenemer_config.show_summary
            window.panel._border_color = self.accent_color
            window.apply_window_border_settings(self.olenemer_config.show_window_border)
            self.update_window(team, tv_data[team])

    def ensure_windows(self) -> None:
        for team in (1, 2):
            if self.get_window(team) is not None:
                continue
            title = "Союзники" if team == 1 else "Противники"
            self.add_window(team, TeamViewData(title=title, rows=[]))

    def show_loading(self, message: str = "Загрузка...") -> None:
        self.ensure_windows()
        for team in (1, 2):
            window = self.get_window(team)
            if window is None:
                continue
            window.show_loading(message)
            window.deiconify()
            window.lift()
            window._ensure_topmost()

    def clear_and_hide(self) -> None:
        for team in (1, 2):
            window = self.get_window(team)
            if window is None:
                continue
            window.clear_content()
            window.withdraw()

    def show_teams(self, tv_data: dict[int, TeamViewData], *, region: str | None = None) -> None:
        if region is not None:
            self.region = region
        self.update_teams(tv_data)
        self.update_idletasks()
        for window in self.windows:
            if window._last_outer_size is not None:
                window._apply_outer_geometry(*window._last_outer_size)
            window.deiconify()
            window.lift()
            window._ensure_topmost()

    def set_opacity(self, opacity: float, *, min_opacity: float = 0.2) -> None:
        opacity = max(min_opacity, min(1.0, opacity))
        self.olenemer_config.window_transparency = opacity
        self.background = background_from_config(self.olenemer_config)
        for window in self.windows:
            if window.winfo_exists():
                window.apply_opacity(opacity)

    def toggle_windows_visibility(self) -> None:
        from lib.olenemer.binds.actions import toggle_windows_visibility as _toggle

        _toggle(self)

    def _current_tv_data(self) -> dict[int, TeamViewData]:
        tv_data: dict[int, TeamViewData] = {}
        for team in (1, 2):
            window = self.get_window(team)
            if window is not None and window._team_data is not None:
                tv_data[team] = window._team_data
        return tv_data

    def apply_settings(self) -> None:
        from lib.olenemer.live.messages import loading_message

        self.olenemer_config = self.config_handler.config.olenemer
        self.background = background_from_config(self.olenemer_config)
        self.accent_color = accent_color_hex(self.config_handler.config.app_global.theme)

        tv_data = self._current_tv_data()
        if tv_data and any(team_data.rows for team_data in tv_data.values()):
            self.column_visibility = ColumnVisibility.from_config_for_battle(
                self.olenemer_config.column_status,
                tv_data,
            )
        else:
            self.column_visibility = ColumnVisibility.from_config(self.olenemer_config.column_status)

        loading_text = loading_message(self.config_handler)
        for window in self.windows:
            if not window.winfo_exists():
                continue
            window.apply_settings(
                background=self.background,
                columns=self.column_visibility,
                border_color=self.accent_color,
                profile_skins=self.olenemer_config.profile_skins,
                tank_display_type=self.olenemer_config.tank_display_type,
                show_border=self.olenemer_config.show_border,
                show_window_border=self.olenemer_config.show_window_border,
                show_summary=self.olenemer_config.show_summary,
            )
            if window.status_label.winfo_ismapped() and not (
                window._team_data and window._team_data.rows
            ):
                window.status_label.configure(text=loading_text)


def run_olenemer_for_replay(
    replay_path: Path | str,
    config_handler: ConfigHandler | None = None,
) -> None:
    prepare_olenemer_tk_env()
    config_handler = config_handler or ConfigHandler()
    olenemer = config_handler.config.olenemer
    tv_data, region, _replay = load_teams_for_replay(
        replay_path,
        profile_skins=olenemer.profile_skins,
    )
    app = OlenemerApp(tv_data, config_handler, region=region)
    from lib.olenemer.binds import OlenemerKeybindManager

    keybinds = OlenemerKeybindManager(app, olenemer.keybinds)
    keybinds.start()
    try:
        app.mainloop()
    finally:
        keybinds.stop()
