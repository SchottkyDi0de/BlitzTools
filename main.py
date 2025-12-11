from kivy import Logger
from kivy.config import Config
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.clock import Clock

from ui.main import MainLayout
from lib.locales.handler import locales
from utils import assets_loader
from lib.config.handler import ConfigHandler

# TESTS
from tests.locales import run; run()  # noqa: E702
ConfigHandler()._rewrite_config()
#

# Load assets
assets_loader.add_assets()
#

_log = Logger

# Configure window
Config.set("graphics", "resizable", int(ConfigHandler().get_config().app_global.window.allow_resize))
Window.minimum_width = ConfigHandler().get_config().app_global.window.width
Window.minimum_height = ConfigHandler().get_config().app_global.window.height
#


class MainApp(MDApp):
    def build(self):
        self.title = "BlitzTools"
        self.theme_cls.dynamic_colors = True
        self.icon = assets_loader.get_asset("images/tools.png")
        self.theme_cls.theme_style = ConfigHandler().get_config().app_global.theming.global_theme
        self.locales = locales
        self.fonts = assets_loader.get_available_fonts()
        self.kivy_config = Config
        self.config = ConfigHandler().get_config().app_global
        self.get_font = assets_loader.get_font
        return MainLayout()

if __name__ == "__main__":
    MainApp().run()
