from __future__ import annotations

import os
from pathlib import Path

from lib.config.handler import ConfigHandler
from lib.config.main_config import ConfigStruct


def expand_config_path(path: str) -> Path:
    expanded = os.path.expandvars(path.replace("/", os.sep))
    return Path(expanded).expanduser()


def live_data_path(recording_folder: Path) -> Path:
    if recording_folder.name.endswith(".wotbreplay"):
        return recording_folder / "data.wotreplay"
    return recording_folder / "data.replay"


def is_recording_folder(path: Path) -> bool:
    if not path.is_dir():
        return False
    name = path.name
    return name.startswith("recording_") and (
        name.endswith(".tbreplay") or name.endswith(".wotbreplay")
    )


def resolve_replay_dirs(config: ConfigStruct) -> list[Path]:
    paths = config.app_global.replay_paths
    regions = config.olenemer.regions
    dirs: list[Path] = []
    if regions.ru and paths.ru:
        dirs.append(expand_config_path(paths.ru))
    if regions.eu and paths.eu:
        dirs.append(expand_config_path(paths.eu))
    return dirs


def replay_dirs_from_handler(handler: ConfigHandler | None = None) -> list[Path]:
    handler = handler or ConfigHandler()
    return resolve_replay_dirs(handler.config)
