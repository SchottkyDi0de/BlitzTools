from __future__ import annotations

from lib.config.handler import ConfigHandler


def loading_message(config_handler: ConfigHandler) -> str:
    language = config_handler.config.app_global.language
    return "Загрузка..." if language == "ru" else "Loading..."
