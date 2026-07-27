from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from lib.config.handler import ConfigHandler
from utils.ui_refresh import refresh_ui


class SettingsScreen(MDScreen):
    name = "settings"

    def on_enter(self, *_args):
        self.load_from_config()

    def load_from_config(self):
        app = MDApp.get_running_app()
        if not app:
            return

        ag = app.config.app_global
        self._sync_font_buttons(ag.font.name)
        self._sync_language_buttons(ag.language)

    def select_font(self, font_name: str):
        app = MDApp.get_running_app()
        if not app:
            return

        app.config.app_global.font.name = font_name
        self._write_config(app)
        refresh_ui(app, apply_theme=False)

    def select_language(self, language: str):
        app = MDApp.get_running_app()
        if not app:
            return

        app.config.app_global.language = language
        self._write_config(app)
        refresh_ui(app, apply_theme=False)

    def _sync_font_buttons(self, selected: str):
        for btn in self.ids.font_group.children:
            if hasattr(btn, "option_value"):
                btn.active = btn.option_value == selected

    def _sync_language_buttons(self, selected: str):
        for btn in self.ids.lang_group.children:
            if hasattr(btn, "option_value"):
                btn.active = btn.option_value == selected

    def _write_config(self, app):
        handler = ConfigHandler()
        handler.config = app.config
        handler.write_config()
