from __future__ import annotations

from pathlib import Path

from lib.config.handler import ConfigHandler
from lib.olenemer.live.poller import LiveReplayPoller
from lib.olenemer.live.paths import replay_dirs_from_handler
from lib.olenemer.live.watchdog import RecordingFolderWatchdog
from lib.olenemer.window.app import OlenemerApp
from lib.olenemer.window.models import TeamViewData
from lib.replay_parser import LiveReplay


def _loading_message(config_handler: ConfigHandler) -> str:
    language = config_handler.config.app_global.language
    return "Загрузка..." if language == "ru" else "Loading..."


class LiveOlenemerController:
    """Coordinates recording-folder watchdog, live parser, and Olenemer UI."""

    def __init__(self, app: OlenemerApp, config_handler: ConfigHandler) -> None:
        self.app = app
        self.config_handler = config_handler
        olenemer = config_handler.config.olenemer
        self._poller = LiveReplayPoller(
            on_teams_ready=self._on_teams_ready,
            profile_skins=olenemer.profile_skins,
        )
        self._watchdog = RecordingFolderWatchdog(
            replay_dirs_from_handler(config_handler),
            on_folder_found=self._on_folder_found,
            on_folder_lost=self._on_folder_lost,
        )

    def start(self) -> None:
        self._watchdog.start()

    def stop(self) -> None:
        self._watchdog.stop()
        self._poller.stop()

    def _on_folder_found(self, folder: Path) -> None:
        self.app.after(0, lambda: self._handle_folder_found(folder))

    def _on_folder_lost(self) -> None:
        self.app.after(0, self._handle_folder_lost)

    def _on_teams_ready(
        self,
        tv_data: dict[int, TeamViewData],
        region: str,
        _replay: LiveReplay,
    ) -> None:
        self.app.after(0, lambda: self.app.show_teams(tv_data, region=region))

    def _handle_folder_found(self, folder: Path) -> None:
        self._poller.start(folder)
        self.app.show_loading(_loading_message(self.config_handler))

    def _handle_folder_lost(self) -> None:
        self._poller.stop()
        self.app.clear_and_hide()
