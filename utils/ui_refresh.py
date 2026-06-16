from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

from utils.app_theme import apply_theme_from_config
from utils.nav import ICON_TO_SCREEN

_ICON_WIDGETS = frozenset({"MDIcon", "Icon"})


def _locale(app: MDApp):
    code = app.config.app_global.language
    if code not in app.locales.data:
        code = "ru"
    return app.locales.data[code].main


def _ui_font(app: MDApp) -> str:
    return app.get_font(app.config.app_global.font.name)


def _apply_fonts(root, app: MDApp) -> None:
    font = _ui_font(app)

    for widget in root.walk():
        if type(widget).__name__ in _ICON_WIDGETS:
            continue
        if not isinstance(widget, (MDLabel, MDTextField)):
            continue
        if getattr(widget, "theme_font_name", None) != "Custom":
            continue
        widget.font_name = font


def _refresh_titlebar(root, app: MDApp, loc) -> None:
    from ui.widgets import ThemeToggleButton

    titlebar = root.ids.titlebar
    titlebar.ids.status_label.text = loc.titlebar.status

    for widget in titlebar.walk():
        if isinstance(widget, ThemeToggleButton):
            widget._sync_icon()


def _refresh_home(root, screen, app: MDApp, loc) -> None:
    ids = root.ids
    ids.home_title.text = loc.home.title
    ids.home_hint.text = loc.home.hint

    modules = loc.modules
    from ui.widgets import FuturaFeatureCard

    for card in screen.walk():
        if not isinstance(card, FuturaFeatureCard):
            continue
        module_key = ICON_TO_SCREEN.get(card.card_icon)
        if not module_key:
            continue
        module = getattr(modules, module_key)
        card.card_title = module.title
        card.card_body = module.body


def _refresh_placeholders(root, loc) -> None:
    from ui.widgets import PlaceholderPane

    for widget in root.walk():
        if not isinstance(widget, PlaceholderPane):
            continue
        widget.pane_title = loc.placeholder.title
        widget.pane_subtitle = loc.placeholder.subtitle


def _refresh_settings(screen, app: MDApp, loc) -> None:
    from ui.widgets import SettingsOptionButton

    settings = loc.settings
    labels = [w for w in screen.walk() if isinstance(w, MDLabel)]
    if labels:
        labels[0].text = settings.title

    section_labels = [w for w in screen.walk() if type(w).__name__ == "SettingsSection"]
    section_texts = [settings.sections.font, settings.sections.language]
    for label, text in zip(section_labels, section_texts):
        label.text = text

    font_labels = {
        "roboto": settings.fonts.roboto,
        "robotomono": settings.fonts.robotomono,
        "jost": settings.fonts.jost,
    }
    lang_labels = {
        "ru": settings.languages.ru,
        "en": settings.languages.en,
    }

    for widget in screen.walk():
        if not isinstance(widget, SettingsOptionButton):
            continue
        if widget.option_value in font_labels:
            widget.option_label = font_labels[widget.option_value]
            widget.active = widget.option_value == app.config.app_global.font.name
            widget.sync_appearance()
        elif widget.option_value in lang_labels:
            widget.option_label = lang_labels[widget.option_value]
            widget.active = widget.option_value == app.config.app_global.language
            widget.sync_appearance()


def _refresh_dvp(screen) -> None:
    if hasattr(screen, "refresh_locale"):
        screen.refresh_locale()


def _refresh_admin_notice(root, loc) -> None:
    from ui.widgets import AdminNoticeBar

    bar = root.ids.get("admin_notice")
    if not isinstance(bar, AdminNoticeBar) or not bar.visible:
        return
    bar.message = loc.admin_notice.message
    bar.sync_appearance()


def refresh_ui(app: MDApp | None = None, *, apply_theme: bool = False) -> None:
    app = app or MDApp.get_running_app()
    if not app or not app.root:
        return

    if apply_theme:
        apply_theme_from_config(app)

    loc = _locale(app)
    root = app.root

    _apply_fonts(root, app)
    _refresh_titlebar(root, app, loc)

    manager = root.ids.screen_manager
    for screen in manager.screens:
        if screen.name == "home":
            _refresh_home(root, screen, app, loc)
        elif screen.name == "settings":
            _refresh_settings(screen, app, loc)
        elif screen.name == "dvp":
            _refresh_dvp(screen)

    _refresh_placeholders(root, loc)
    _refresh_admin_notice(root, loc)
