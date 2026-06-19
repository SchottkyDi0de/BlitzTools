from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from pynput.keyboard import Key, Listener

from lib.dataclasses.configs.main_config import OlenemerKeybinds
from lib.olenemer.binds.actions import adjust_opacity, toggle_windows_visibility
from lib.olenemer.binds.keys import parse_keybind

if TYPE_CHECKING:
    from lib.olenemer.window.app import OlenemerApp


class OlenemerKeybindManager:
    """Global hotkeys for the olenemer (pynput listener in a background thread)."""

    def __init__(
        self,
        app: OlenemerApp,
        keybinds: OlenemerKeybinds,
        *,
        opacity_step: float = 0.05,
        action_cooldown: float = 0.1,
    ) -> None:
        self._app = app
        self._opacity_step = opacity_step
        self._action_cooldown = action_cooldown
        self._listener: Listener | None = None
        self._thread: threading.Thread | None = None
        self._pressed: set[Key] = set()
        self._last_action_at: dict[Key, float] = {}

        self._actions: dict[Key, Callable[[], None]] = {}
        self._register(keybinds.show_hide, self._toggle_visibility)
        self._register(keybinds.increase_opacity, self._increase_opacity)
        self._register(keybinds.decrease_opacity, self._decrease_opacity)

    def _register(self, key_name: str, action: Callable[[], None]) -> None:
        key = parse_keybind(key_name)
        if key is None:
            return
        self._actions[key] = action

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        def run() -> None:
            with Listener(on_press=self._on_press, on_release=self._on_release) as listener:
                self._listener = listener
                listener.join()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key: Key) -> None:
        action = self._actions.get(key)
        if action is None:
            return
        if key in self._pressed:
            return

        now = time.time()
        last = self._last_action_at.get(key, 0.0)
        if now - last < self._action_cooldown:
            return

        self._pressed.add(key)
        self._last_action_at[key] = now
        self._app.after(0, action)

    def _on_release(self, key: Key) -> None:
        self._pressed.discard(key)

    def _toggle_visibility(self) -> None:
        toggle_windows_visibility(self._app)

    def _increase_opacity(self) -> None:
        adjust_opacity(self._app, self._opacity_step)

    def _decrease_opacity(self) -> None:
        adjust_opacity(self._app, -self._opacity_step)
