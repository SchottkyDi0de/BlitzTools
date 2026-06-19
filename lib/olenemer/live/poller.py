from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from pathlib import Path
from time import sleep

from lib.olenemer.live.paths import live_data_path
from lib.olenemer.window.models import TeamViewData
from lib.olenemer.window.service import load_teams_for_replay
from lib.replay_parser import LiveReplay
from lib.replay_parser.errors import ReplayParserError


class LiveReplayPoller:
    """Polls data.replay inside a recording folder until players are found, then stops."""

    def __init__(
        self,
        *,
        on_teams_ready: Callable[[dict[int, TeamViewData], str, LiveReplay], None],
        poll_interval: float = 1.0,
        profile_skins: bool = True,
    ) -> None:
        self.on_teams_ready = on_teams_ready
        self.poll_interval = poll_interval
        self.profile_skins = profile_skins
        self._folder: Path | None = None
        self._stop = False
        self._thread: threading.Thread | None = None

    def start(self, recording_folder: Path) -> None:
        self.stop()
        self._folder = recording_folder
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True
        self._folder = None

    def _run(self) -> None:
        while not self._stop and self._folder is not None:
            folder = self._folder
            data_path = live_data_path(folder)
            try:
                if data_path.is_file():
                    tv_data, region, replay = load_teams_for_replay(
                        data_path,
                        profile_skins=self.profile_skins,
                    )
                    if not self._stop and self._folder == folder:
                        self.on_teams_ready(tv_data, region, replay)
                        return
            except ReplayParserError as exc:
                if "No players found" not in str(exc):
                    traceback.print_exc()
            except FileNotFoundError:
                pass
            except Exception:
                traceback.print_exc()

            if self._stop:
                break
            sleep(self.poll_interval)
