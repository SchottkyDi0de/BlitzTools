import platform

from kivy import Logger
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.relativelayout import MDRelativeLayout

from ui.main import MainLayout
from lib.locales.handler import locales

# TESTS
from tests.locales import run; run()  # noqa: E702
#

_log = Logger


_platform_release = platform.release()
_platform_system = platform.system()

_log.info(f'Platform: SYSTEM: {_platform_system} RELEASE: {_platform_release}')
if _platform_system == "Windows":
    import pywinstyles
    pywinstyles.apply_style(Window, style="acrylic")
    if int(platform.release()) >= 11:
        _log.info('Style: pywinstyles fully support detected')
        accent_color = pywinstyles.get_accent_color()
        _log.info(f'Accent color: {accent_color}')
        # pywinstyles.change_header_color(Window, accent_color)


def __set_win_style():
    
    Window.size = (800, 400)

class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.locales = locales
        return MainLayout()

if __name__ == "__main__":
    # __set_win_style()
    MainApp().run()
