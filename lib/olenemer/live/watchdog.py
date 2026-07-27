from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from time import sleep

from lib.olenemer.live.paths import is_recording_folder


class RecordingFolderWatchdog:
    """Polls replay directories for recording_* folders (live battle)."""

    def __init__(
        self,
        replay_dirs: list[Path],
        *,
        on_folder_found: Callable[[Path], None],
        on_folder_lost: Callable[[], None],
        poll_interval: float = 1.0,
    ) -> None:
        self.replay_dirs = list(replay_dirs)
        self.on_folder_found = on_folder_found
        self.on_folder_lost = on_folder_lost
        self.poll_interval = poll_interval
        self._active: Path | None = None
        self._stop = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop = True

    def _scan(self) -> list[Path]:
        folders: list[Path] = []
        for replay_dir in self.replay_dirs:
            if not replay_dir.is_dir():
                continue
            try:
                for entry in replay_dir.iterdir():
                    if is_recording_folder(entry):
                        folders.append(entry)
            except OSError:
                continue
        return folders

    @staticmethod
    def _pick_active(folders: list[Path]) -> Path | None:
        if not folders:
            return None
        return max(folders, key=lambda path: path.stat().st_mtime)

    def _run(self) -> None:
        while not self._stop:
            current = self._pick_active(self._scan())

            if current is None and self._active is not None:
                self._active = None
                self.on_folder_lost()
            elif current is not None and current != self._active:
                if self._active is not None:
                    self._active = None
                    self.on_folder_lost()
                self._active = current
                self.on_folder_found(current)

            sleep(self.poll_interval)
