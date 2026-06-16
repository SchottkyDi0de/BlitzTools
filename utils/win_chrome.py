import platform
from ctypes import windll

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.app import MDApp

from utils.config_persist import pause_geometry_persist, resume_geometry_persist

WM_NCLBUTTONDOWN = 0xA1
HTCAPTION = 2

_window_state: dict | None = None
_chrome_animating = False
_closing = False


def is_chrome_animating() -> bool:
    return _chrome_animating or _closing


def reset_chrome_state() -> None:
    global _chrome_animating, _closing
    _chrome_animating = False
    _closing = False


def apply_window_settings(config) -> None:
    window_cfg = config.app_global.window
    pause_geometry_persist()
    Window.borderless = True
    Window.size = (window_cfg.width, window_cfg.height)
    Window.left = window_cfg.pos[0]
    Window.top = window_cfg.pos[1]
    Window.set_title("BlitzTools")
    _remember_window_state()
    resume_geometry_persist()


def _remember_window_state() -> None:
    global _window_state
    _window_state = {
        "size": tuple(Window.size),
        "left": Window.left,
        "top": Window.top,
    }


def _apply_window_state(config=None) -> None:
    pause_geometry_persist()
    if _window_state:
        Window.size = _window_state["size"]
        Window.left = _window_state["left"]
        Window.top = _window_state["top"]
    elif config is not None:
        window_cfg = config.app_global.window
        Window.size = (window_cfg.width, window_cfg.height)
        Window.left = window_cfg.pos[0]
        Window.top = window_cfg.pos[1]
    resume_geometry_persist()


def _get_root():
    app = MDApp.get_running_app()
    return app.root if app else None


def _fade_out(content, callback, *, duration=0.18, slide=12) -> bool:
    global _chrome_animating
    if _chrome_animating:
        return False

    _chrome_animating = True
    start_y = content.y

    anim = (
        Animation(opacity=0, duration=duration, t="out_cubic")
        & Animation(y=start_y - dp(slide), duration=duration, t="out_cubic")
    )

    def _done(*_args):
        global _chrome_animating
        _chrome_animating = False
        callback()

    anim.bind(on_complete=_done)
    anim.start(content)
    return True


def drag_window() -> None:
    if platform.system() != "Windows" or is_chrome_animating():
        return
    hwnd = windll.user32.GetActiveWindow()
    windll.user32.ReleaseCapture()
    windll.user32.SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)


def minimize() -> None:
    root = _get_root()
    if root is None:
        Window.minimize()
        return

    if is_chrome_animating():
        return

    _remember_window_state()

    def _finish_minimize():
        root.opacity = 1
        root.y = 0
        Window.minimize()

    if not _fade_out(root, _finish_minimize, duration=0.18, slide=10):
        Window.minimize()


def close() -> None:
    global _closing
    if _closing:
        return

    root = _get_root()
    if root is None:
        Window.close()
        return

    if is_chrome_animating():
        return

    _closing = True

    def _finish_close():
        Window.close()

    if not _fade_out(root, _finish_close, duration=0.16, slide=14):
        Window.close()


def restore_window_appearance(config=None) -> None:
    def _do_restore(_dt):
        root = _get_root()
        if root is None:
            return

        reset_chrome_state()
        _apply_window_state(config)
        _remember_window_state()
        root.y = 0
        root.opacity = 0
        Animation(opacity=1, duration=0.22, t="in_quad").start(root)

    Clock.schedule_once(_do_restore, 0)
