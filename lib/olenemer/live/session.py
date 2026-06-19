from __future__ import annotations

from lib.config.handler import ConfigHandler
from lib.olenemer.live.controller import LiveOlenemerController
from lib.olenemer.window.app import OlenemerApp
from lib.olenemer.window.tcl_env import configure_tcl_tk


def run_olenemer_live(config_handler: ConfigHandler | None = None) -> None:
    configure_tcl_tk()
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
