import platform

from utils.dpi_awareness import enable_dpi_awareness

if platform.system() == "Windows":
    enable_dpi_awareness()

from kivy.config import Config

if platform.system() == "Windows":
    Config.set("graphics", "borderless", "1")

Config.set("input", "mouse", "mouse,disable_multitouch")

from utils.startup_config import apply_early_window_config

apply_early_window_config()

from kivy import Logger
from threading import Thread

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import DictProperty
from kivymd.app import MDApp

from utils.quiet_loggers import quiet_third_party_loggers

quiet_third_party_loggers()

from ui.main import MainLayout
from lib.api import BlitzAPI
from lib.config.handler import ConfigHandler
from lib.locales.handler import locales
from ui.widgets import ensure_hover_listener
from utils import assets_loader
from utils.admin import needs_admin_notice
from utils.app_theme import apply_theme_from_config, get_palette, sync_feature_cards
from utils.config_persist import bind_window_geometry_persist, sync_window_geometry
from utils.screen_layout import prepare_screens, prepare_screens_delayed
from utils.ui_refresh import refresh_ui, titlebar_status_text
from utils.ui_scale import apply_ui_scale
from utils.win_chrome import apply_window_settings, reset_chrome_state, restore_window_appearance

assets_loader.add_assets()

_log = Logger


class MainApp(MDApp):
    palette = DictProperty({})
    use_kivy_settings = False

    def open_settings(self, *_args):
        return True

    def build(self):
        reset_chrome_state()
        self.icon = "images/icon.png"
        self.title = "BlitzTools"
        self.config = ConfigHandler().get_config()

        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style_switch_animation = False
        self.theme_cls.theme_style = (
            "Light" if self.config.app_global.theme == "light" else "Dark"
        )
        for key, value in get_palette(self.config.app_global.theme).items():
            self.palette[key] = value

        self.locales = locales
        self.fonts = assets_loader.get_available_fonts()
        self.get_font = assets_loader.get_font

        window_cfg = self.config.app_global.window
        apply_ui_scale(window_cfg.width, window_cfg.height)

        root = MainLayout()
        apply_theme_from_config(self)
        apply_window_settings(self.config)
        from utils.app_icon import apply_kivy_app_icon

        apply_kivy_app_icon(self)
        return root

    def on_start(self):
        Clock.schedule_once(self._finish_start, 0)

    def _finish_start(self, _dt):
        if not self.root:
            return
        from utils.app_icon import apply_kivy_app_icon

        refresh_ui(self, apply_theme=True)
        self._maybe_show_admin_notice()
        prepare_screens(self.root)
        prepare_screens_delayed(self.root, 0.05)
        prepare_screens_delayed(self.root, 0.2)
        self.root.y = 0
        self.root.opacity = 1
        if not getattr(self, "_layout_bound", False):
            self._layout_bound = True
            Window.bind(on_resize=self._on_window_resize)
        ensure_hover_listener()
        manager = self.root.ids.screen_manager
        if not getattr(self, "_screen_bound", False):
            self._screen_bound = True
            manager.bind(current=self._on_screen_changed)
        Clock.schedule_once(self._bind_geometry, 0.3)
        Clock.schedule_once(lambda _dt: apply_window_settings(self.config), 0.05)
        Clock.schedule_once(lambda _dt: apply_kivy_app_icon(self), 0.1)
        Clock.schedule_once(lambda _dt: apply_kivy_app_icon(self), 0.35)
        self._fetch_app_version()

    def _fetch_app_version(self):
        def worker():
            version = BlitzAPI().get_version()
            if version:
                Clock.schedule_once(lambda _dt, v=version: self._apply_app_version(v), 0)

        Thread(target=worker, daemon=True).start()

    def _apply_app_version(self, version: str):
        if not self.root:
            return
        self._remote_version = version
        self.root.ids.titlebar.ids.status_label.text = titlebar_status_text(self)

    def _maybe_show_admin_notice(self):
        if not needs_admin_notice() or not self.root:
            return

        code = self.config.app_global.language
        if code not in self.locales.data:
            code = "ru"
        message = self.locales.data[code].main.admin_notice.message
        self.root.ids.admin_notice.show(message)

    def _on_screen_changed(self, _manager, screen_name: str):
        if screen_name == "home" and self.root:
            from ui.widgets import relayout_feature_cards

            relayout_feature_cards(self.root)
            sync_feature_cards(self.root)
            Clock.schedule_once(
                lambda _dt: sync_feature_cards(self.root) if self.root else None,
                0.05,
            )

    def _on_window_resize(self, *_args):
        if not self.root:
            return
        prepare_screens(self.root)

    def _bind_geometry(self, _dt):
        bind_window_geometry_persist(self.config)

    def on_stop(self):
        from lib.olenemer.service import get_olenemer_runtime

        get_olenemer_runtime().stop()
        sync_window_geometry(self.config)
        ConfigHandler().config = self.config
        ConfigHandler().write_config()

    def on_resume(self):
        restore_window_appearance(self.config)
        return True


if __name__ == "__main__":
    MainApp().run()
