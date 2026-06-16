import platform

from kivy.config import Config

if platform.system() == "Windows":
    Config.set("graphics", "borderless", "1")

from utils.startup_config import apply_early_window_config

apply_early_window_config()

from kivy import Logger
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import DictProperty
from kivymd.app import MDApp

from ui.main import MainLayout
from lib.locales.handler import locales
from utils import assets_loader
from lib.config.handler import ConfigHandler
from utils.app_theme import apply_theme_from_config, get_palette, sync_feature_cards
from utils.config_persist import bind_window_geometry_persist, sync_window_geometry
from utils.screen_layout import prepare_screens, prepare_screens_delayed
from utils.ui_refresh import refresh_ui
from utils.ui_scale import apply_ui_scale
from utils.win_chrome import apply_window_settings, reset_chrome_state, restore_window_appearance
# TESTS
from tests.locales import run; run()  # noqa: E702
#

# Load assets
assets_loader.add_assets()
#

_log = Logger


class MainApp(MDApp):
    palette = DictProperty({})

    def build(self):
        reset_chrome_state()
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
        return root

    def on_start(self):
        Clock.schedule_once(self._finish_start, 0)

    def _finish_start(self, _dt):
        if not self.root:
            return
        refresh_ui(self, apply_theme=True)
        prepare_screens(self.root)
        prepare_screens_delayed(self.root, 0.05)
        prepare_screens_delayed(self.root, 0.2)
        self.root.y = 0
        self.root.opacity = 1
        if not getattr(self, "_layout_bound", False):
            self._layout_bound = True
            Window.bind(on_resize=self._on_window_resize)
        manager = self.root.ids.screen_manager
        if not getattr(self, "_screen_bound", False):
            self._screen_bound = True
            manager.bind(current=self._on_screen_changed)
        Clock.schedule_once(self._bind_geometry, 0.3)
        Clock.schedule_once(lambda _dt: apply_window_settings(self.config), 0.05)

    def _on_screen_changed(self, _manager, screen_name: str):
        if screen_name == "home" and self.root:
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
        sync_window_geometry(self.config)
        ConfigHandler().config = self.config
        ConfigHandler().write_config()

    def on_resume(self):
        restore_window_appearance(self.config)
        return True


if __name__ == "__main__":
    MainApp().run()
