from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from lib.config.handler import ConfigHandler

if TYPE_CHECKING:
    from lib.olenemer.binds import OlenemerKeybindManager
    from lib.olenemer.live.controller import LiveOlenemerController
    from lib.olenemer.window.app import OlenemerApp


class OlenemerRuntime:
    """Runs the CTk olenemer overlay in a background thread."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._app: OlenemerApp | None = None
        self._controller: LiveOlenemerController | None = None
        self._keybinds: OlenemerKeybindManager | None = None
        self._lock = threading.Lock()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self, config_handler: ConfigHandler | None = None) -> bool:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False

            config_handler = config_handler or ConfigHandler()

            def run() -> None:
                from utils.quiet_loggers import quiet_third_party_loggers

                quiet_third_party_loggers()
                from lib.olenemer.window.app import OlenemerApp
                from lib.olenemer.live.controller import LiveOlenemerController
                from lib.olenemer.window.tcl_env import prepare_olenemer_tk_env

                prepare_olenemer_tk_env()
                from lib.olenemer.binds import OlenemerKeybindManager

                app = OlenemerApp.for_live(config_handler)
                controller = LiveOlenemerController(app, config_handler)
                keybinds = OlenemerKeybindManager(app, config_handler.config.olenemer.keybinds)
                self._app = app
                self._controller = controller
                self._keybinds = keybinds
                controller.start()
                keybinds.start()
                try:
                    app.mainloop()
                finally:
                    keybinds.stop()
                    controller.stop()
                    self._app = None
                    self._controller = None
                    self._keybinds = None
                    self._thread = None

            self._thread = threading.Thread(target=run, daemon=True)
            self._thread.start()
            return True

    def stop(self) -> None:
        app = self._app
        if app is None:
            return
        try:
            app.after(0, app.destroy)
        except Exception:
            pass

    def apply_config(self) -> None:
        app = self._app
        if app is None or not self.is_running():
            return

        controller = self._controller
        keybinds = self._keybinds

        def _apply() -> None:
            if controller is not None:
                controller.apply_config()
            app.apply_settings()
            if keybinds is not None:
                keybinds.reload(app.config_handler.config.olenemer.keybinds)

        try:
            app.after(0, _apply)
        except Exception:
            pass


_runtime: OlenemerRuntime | None = None


def get_olenemer_runtime() -> OlenemerRuntime:
    global _runtime
    if _runtime is None:
        _runtime = OlenemerRuntime()
    return _runtime
