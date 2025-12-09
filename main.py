import platform

from kivy import Logger
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.clock import Clock

from ui.main import MainLayout
from lib.locales.handler import locales
from utils import assets_loader
from lib.config.handler import ConfigHandler

# TESTS
from tests.locales import run; run()  # noqa: E702
#

# Load assets
assets_loader.add_assets()
#

_log = Logger


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.locales = locales
        self.fonts = assets_loader.get_available_fonts()
        self.config = ConfigHandler().get_config()
        self.get_font = assets_loader.get_font
        return MainLayout()

if __name__ == "__main__":
    MainApp().run()
