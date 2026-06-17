import yaml

from utils.resource_path import get_current_directory, get_files_path
from utils.window_geometry import (
    is_valid_window_pos,
    is_valid_window_size,
    migrate_legacy_window_size_dict,
)


def read_window_config() -> dict:
    default_path = get_current_directory().joinpath("config/default_config.yaml")
    config_path = get_files_path().joinpath("config/config.yaml")

    with open(default_path, "r", encoding="utf-8") as f:
        default_data = yaml.safe_load(f) or {}

    default_window = default_data["app_global"]["window"]
    window = dict(default_window)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_data = yaml.safe_load(f) or {}
            user_window = user_data.get("app_global", {}).get("window")
            if isinstance(user_window, dict):
                window.update(user_window)
        except (OSError, yaml.YAMLError, TypeError, KeyError):
            pass

    migrate_legacy_window_size_dict(window, default_window)

    if not is_valid_window_size(int(window["width"]), int(window["height"])):
        window["width"] = default_window["width"]
        window["height"] = default_window["height"]

    if not is_valid_window_pos(window.get("pos")):
        window["pos"] = list(default_window["pos"])

    return window


def apply_early_window_config() -> None:
    from kivy.config import Config

    window = read_window_config()
    Config.set("graphics", "width", str(window["width"]))
    Config.set("graphics", "height", str(window["height"]))
