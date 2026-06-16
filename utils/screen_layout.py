from kivy.clock import Clock
from kivy.graphics import Scale
from kivymd.app import MDApp

_SCROLL_TYPES = frozenset({"MDScrollView", "ScrollView"})


def _screen_in_manager(screen, manager) -> bool:
    if screen is None or manager is None:
        return False
    parent = screen.parent
    return parent is manager or parent == manager


def reset_screen_visual_state(root) -> None:
    manager = root.ids.screen_manager
    for screen in manager.screens:
        screen.opacity = 1
        for canvas in (screen.canvas.before, screen.canvas.after):
            for instr in canvas.children:
                if isinstance(instr, Scale):
                    instr.xyz = (1, 1, 1)
        for widget in screen.walk():
            scale = getattr(widget, "_internal_scale", None)
            if scale is not None:
                scale.xyz = (1, 1, 1)

    screen = manager.current_screen
    if _screen_in_manager(screen, manager):
        screen.pos = manager.pos
        screen.size = manager.size


def normalize_current_screen(root) -> None:
    reset_screen_visual_state(root)


def fix_scroll_content(root) -> None:
    manager = root.ids.screen_manager
    for screen in manager.screens:
        if not _screen_in_manager(screen, manager):
            continue
        for widget in screen.walk():
            if type(widget).__name__ not in _SCROLL_TYPES:
                continue
            if not widget.children:
                continue
            inner = widget.children[0]
            inner.do_layout()
            min_h = getattr(inner, "minimum_height", 0)
            if min_h > inner.height:
                inner.height = min_h


def prepare_screens(root, *, reapply_theme: bool = False) -> None:
    reset_screen_visual_state(root)
    fix_scroll_content(root)
    root.ids.screen_manager.do_layout()

    if reapply_theme:
        from utils.app_theme import apply_theme_from_config

        app = MDApp.get_running_app()
        if app:
            apply_theme_from_config(app)


def prepare_screens_delayed(root, delay: float = 0, *, reapply_theme: bool = False) -> None:
    Clock.schedule_once(
        lambda _dt: prepare_screens(root, reapply_theme=reapply_theme),
        delay,
    )
