from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from ui.settings_screen import SettingsScreen  # noqa: F401
from ui.widgets import (  # noqa: F401
    CustomTitleBar,
    FuturaFeatureCard,
    FuturaNavButton,
    SettingsOptionButton,
    StatusDot,
    ThemeToggleButton,
    TitleBarButton,
)

Builder.load_file("ui/kv/titlebar.kv")
Builder.load_file("ui/kv/screens/settings.kv")
Builder.load_file("ui/kv/main.kv")

class MainLayout(MDBoxLayout):
    pass
