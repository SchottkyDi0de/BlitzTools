from __future__ import annotations

from lib.config.handler import ConfigHandler
from lib.olenemer.live.controller import LiveOlenemerController
from lib.olenemer.window.app import OlenemerApp
from lib.olenemer.window.tcl_env import prepare_olenemer_tk_env


def run_olenemer_live(config_handler: ConfigHandler | None = None) -> None:
    prepare_olenemer_tk_env()
    config_handler = config_handler or ConfigHandler()
    app = OlenemerApp.for_live(config_handler)
    controller = LiveOlenemerController(app, config_handler)
    from lib.olenemer.binds import OlenemerKeybindManager

    keybinds = OlenemerKeybindManager(app, config_handler.config.olenemer.keybinds)
    controller.start()
    keybinds.start()
    try:
        app.mainloop()
    finally:
        keybinds.stop()
        controller.stop()
