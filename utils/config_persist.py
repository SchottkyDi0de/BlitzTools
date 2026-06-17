from kivy.clock import Clock
from kivy.core.window import Window

from lib.config.handler import ConfigHandler
from utils.window_geometry import is_valid_window_size

_save_event = None
_geometry_sync_enabled = False
_persist_callback = None
_bound_config = None
_startup_grace_event = None


def sync_window_geometry(config, *, include_size: bool = True) -> None:
    width = int(Window.width)
    height = int(Window.height)
    if include_size and not is_valid_window_size(width, height):
        return

    if include_size:
        config.app_global.window.width = width
        config.app_global.window.height = height
    config.app_global.window.pos = [int(Window.left), int(Window.top)]


def persist_config(config) -> None:
    handler = ConfigHandler()
    handler.config = config
    handler.write_config()


def _schedule_persist(*_args):
    global _save_event
    if not _geometry_sync_enabled or _bound_config is None:
        return

    sync_window_geometry(_bound_config, include_size=False)

    if _save_event is not None:
        _save_event.cancel()
    _save_event = Clock.schedule_once(
        lambda _dt: persist_config(_bound_config), 0.4
    )


def bind_window_geometry_persist(config) -> None:
    global _geometry_sync_enabled, _bound_config, _persist_callback, _startup_grace_event
    _bound_config = config
    _geometry_sync_enabled = False
    if _persist_callback is None:
        _persist_callback = _schedule_persist
        Window.bind(on_move=_persist_callback, on_resize=_persist_callback)

    if _startup_grace_event is not None:
        _startup_grace_event.cancel()
    _startup_grace_event = Clock.schedule_once(_enable_geometry_persist, 1.5)


def _enable_geometry_persist(_dt) -> None:
    global _geometry_sync_enabled, _startup_grace_event
    _startup_grace_event = None
    _geometry_sync_enabled = True


def unbind_window_geometry_persist() -> None:
    global _geometry_sync_enabled, _save_event, _persist_callback, _startup_grace_event
    _geometry_sync_enabled = False
    if _startup_grace_event is not None:
        _startup_grace_event.cancel()
        _startup_grace_event = None
    if _persist_callback is not None:
        Window.unbind(on_move=_persist_callback, on_resize=_persist_callback)
        _persist_callback = None
    if _save_event is not None:
        _save_event.cancel()
        _save_event = None


def pause_geometry_persist():
    global _geometry_sync_enabled
    _geometry_sync_enabled = False


def resume_geometry_persist():
    global _geometry_sync_enabled
    _geometry_sync_enabled = True
