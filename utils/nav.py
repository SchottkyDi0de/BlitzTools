ICON_TO_SCREEN = {
    "chart-timeline-variant": "sessions",
    "target": "olenemer",
    "shield-lock-outline": "cluster",
    "filmstrip-box": "replay",
    "file-swap-outline": "dvp",
    "palette-outline": "ui_manager",
}

SCREEN_ORDER = [
    "home",
    "sessions",
    "olenemer",
    "cluster",
    "replay",
    "dvp",
    "ui_manager",
    "settings",
]


def navigate_to(screen_name: str) -> None:
    from kivy.clock import Clock
    from kivymd.app import MDApp

    from ui.widgets import FuturaNavButton
    from utils.screen_layout import prepare_screens

    app = MDApp.get_running_app()
    if not app or not app.root:
        return

    root = app.root
    manager = root.ids.screen_manager
    current = manager.current

    if current != screen_name:
        transition = manager.transition
        if hasattr(transition, "direction"):
            try:
                old_i = SCREEN_ORDER.index(current)
                new_i = SCREEN_ORDER.index(screen_name)
                transition.direction = "left" if new_i > old_i else "right"
            except ValueError:
                transition.direction = "left"
        if hasattr(transition, "duration"):
            transition.duration = 0.22
        manager.current = screen_name
        duration = getattr(transition, "duration", 0.22)

        def _after_transition(_dt):
            prepare_screens(root)
            if getattr(app, "palette", None):
                from utils.app_theme import sync_feature_cards, sync_icon_colors

                sync_feature_cards(root)
                sync_icon_colors(root, app.palette)

        Clock.schedule_once(_after_transition, duration + 0.02)

    if screen_name != "home":
        from ui.widgets import clear_feature_card_hover

        clear_feature_card_hover(root)

    for child in root.ids.nav_panel.walk():
        if isinstance(child, FuturaNavButton):
            child.active = child.screen_name == screen_name

    if getattr(app, "palette", None):
        from utils.app_theme import _sync_nav_buttons, sync_feature_cards, sync_icon_colors

        _sync_nav_buttons(root, app.palette)

        def _deferred_card_sync(_dt):
            sync_feature_cards(root)
            sync_icon_colors(root, app.palette)

        Clock.schedule_once(_deferred_card_sync, 0)
