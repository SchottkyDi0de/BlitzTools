from __future__ import annotations

from datetime import datetime
from threading import Thread

from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from lib.replay_parser.errors import ReplayParserError
from lib.replay_parser.models.region import Region, region_from_filename
from lib.replay_parser.presenter import ReplayBattleView, parse_replay_file
from ui.replay_widgets import sync_inline_marks
from utils.file_dialogs import pick_files


def _format_duration(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def _format_battle_time(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone().strftime("%d.%m.%Y %H:%M")


class ReplayScreen(MDScreen):
    name = "replay"

    def __init__(self, **kwargs):
        self._busy = False
        self._view: ReplayBattleView | None = None
        super().__init__(**kwargs)

    def on_enter(self, *_args):
        self.refresh_locale()

    def _locale(self):
        app = MDApp.get_running_app()
        code = app.config.app_global.language
        if code not in app.locales.data:
            code = "ru"
        return app.locales.data[code].main.replay

    def _language(self) -> str:
        app = MDApp.get_running_app()
        code = app.config.app_global.language
        return code if code in app.locales.data else "ru"

    def refresh_locale(self):
        loc = self._locale()
        self.ids.screen_title.text = loc.title
        self.ids.pick_replay_btn.action_label = loc.actions.pick_replay
        self.ids.author_stats_title.text = loc.author.title
        if not self._busy and self._view is None:
            self.ids.status_label.text = loc.status.idle

        for panel in (self.ids.team1_panel, self.ids.team2_panel):
            panel.refresh_columns(loc.columns)

        if self._view is not None:
            self._apply_view(self._view)

    def pick_replay(self):
        if self._busy:
            return
        loc = self._locale()
        paths = pick_files(
            title=loc.actions.pick_replay_dialog,
            filetypes=[
                ("WoT Blitz replay", "*.wotbreplay;*.tbreplay"),
                ("EU replay", "*.wotbreplay"),
                ("RU replay", "*.tbreplay"),
                ("All files", "*.*"),
            ],
        )
        if not paths:
            return
        self._start_parse(paths[0])

    def _start_parse(self, path: str):
        self._busy = True
        loc = self._locale()
        self.ids.status_label.text = loc.status.loading.format(name=path.split("\\")[-1].split("/")[-1])
        self._hide_results()

        language = self._language()
        Thread(target=self._parse_worker, args=(path, language), daemon=True).start()

    def _parse_worker(self, path: str, language: str):
        error = None
        view = None
        try:
            view = self._parse_with_region_fallback(path, language)
        except ReplayParserError as exc:
            error = str(exc)
        except Exception as exc:
            error = str(exc)

        Clock.schedule_once(lambda _dt: self._on_parse_done(view, error), 0)

    def _parse_with_region_fallback(self, path: str, language: str) -> ReplayBattleView:
        primary = region_from_filename(path)
        secondary = Region.RU if primary == Region.EU else Region.EU
        last_error: Exception | None = None
        for region in (primary, secondary):
            try:
                return parse_replay_file(path, region, language=language)
            except Exception as exc:
                last_error = exc
        if last_error is not None:
            raise last_error
        raise ReplayParserError("failed to parse replay")

    def _on_parse_done(self, view: ReplayBattleView | None, error: str | None):
        self._busy = False
        loc = self._locale()
        if error or view is None:
            self._view = None
            self.ids.status_label.text = loc.status.error.format(error=error or "unknown")
            self._hide_results()
            return

        self._view = view
        self.ids.status_label.text = loc.status.ready.format(name=view.recorder_name)
        self._apply_view(view)
        self._show_results()

    def _apply_view(self, view: ReplayBattleView):
        loc = self._locale()
        if view.winner_team == 1:
            winner_text = loc.summary.winner_team1
        elif view.winner_team == 2:
            winner_text = loc.summary.winner_team2
        else:
            winner_text = loc.summary.draw

        self.ids.winner_label.text = winner_text
        self._apply_battle_meta(view, loc)
        self._apply_author_stats(view, loc)

        self.ids.team1_panel.team_title = loc.teams.team1
        self.ids.team2_panel.team_title = loc.teams.team2
        self.ids.team1_panel.set_players(
            view.team1,
            is_winner=view.winner_team == 1,
            is_loser=view.winner_team == 2,
            win_label=loc.teams.winner,
            lose_label=loc.teams.defeat,
        )
        self.ids.team2_panel.set_players(
            view.team2,
            is_winner=view.winner_team == 2,
            is_loser=view.winner_team == 1,
            win_label=loc.teams.winner,
            lose_label=loc.teams.defeat,
        )

    def _apply_battle_meta(self, view: ReplayBattleView, loc) -> None:
        meta_parts = [
            loc.summary.meta_date.format(date=_format_battle_time(view.battle_time)),
            loc.summary.meta_duration.format(duration=_format_duration(view.duration_secs)),
            loc.summary.meta_mode.format(mode=view.room_type_label),
            loc.summary.meta_map_id.format(id=view.map_id),
        ]
        self.ids.meta_label.text = "\n".join(meta_parts)

    def _apply_author_stats(self, view: ReplayBattleView, loc) -> None:
        self.ids.author_battle_line.text = loc.summary.battle_author.format(name=view.recorder_name)
        self.ids.author_stats_header.text = loc.summary.author_id.format(id=view.author_account_id or "—")
        self.ids.author_tank_line.text = f"{loc.summary.author_tank} {view.author_tank_label}"

        marks = self.ids.author_marks
        marks.marks_count = view.author_marks
        marks._rebuild_marks()
        Clock.schedule_once(lambda _dt: self._sync_author_tank_row(), 0)

        body_parts = [
            loc.summary.author_damage.format(value=view.author_damage),
            loc.summary.earnings_header,
            loc.summary.earnings_silver.format(value=view.author_credits),
            loc.summary.earnings_xp.format(value=view.author_xp),
            loc.summary.earnings_free_xp.format(value=view.free_xp),
        ]
        self.ids.author_stats_label.text = "\n".join(body_parts)

    def _sync_author_tank_row(self) -> None:
        row = self.ids.author_tank_row
        if row.width <= 0:
            Clock.schedule_once(lambda _dt: self._sync_author_tank_row(), 0)
            return
        sync_inline_marks(
            self.ids.author_tank_line,
            self.ids.author_marks,
            marks_count=int(self.ids.author_marks.marks_count),
            max_width=row.width,
            gap=row.spacing,
        )
        Clock.schedule_once(lambda _dt: self.ids.author_marks._sync_text_size(), 0)

    def _show_results(self):
        for box_id in ("summary_box", "teams_box"):
            box = self.ids[box_id]
            box.opacity = 1
            box.disabled = False
            box.height = box.minimum_height
        self._refresh_content_height(reset_scroll=True)

    def _hide_results(self):
        for box_id in ("summary_box", "teams_box"):
            box = self.ids[box_id]
            box.opacity = 0
            box.disabled = True
            box.height = 0
        self.ids.team1_panel.ids.rows_box.clear_widgets()
        self.ids.team2_panel.ids.rows_box.clear_widgets()
        self._refresh_content_height(reset_scroll=False)

    def _refresh_content_height(self, *, reset_scroll: bool):
        content = self.ids.content_box
        content.height = content.minimum_height
        if reset_scroll:
            self.ids.content_scroll.scroll_y = 1
        Clock.schedule_once(self._sync_scroll_height, 0)

    def _sync_scroll_height(self, _dt):
        content = self.ids.content_box
        content.height = content.minimum_height
