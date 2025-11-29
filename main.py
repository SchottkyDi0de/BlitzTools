# Импорты библиотек
import dearpygui.dearpygui as dpg

# Импорты из проекта
from utils.resource_path import get_current_directory
from utils.font_loader import get_font, load_font_dpg
from utils.logger import get_logger
from lib.db.database import Database
from utils.exc_wrapper import wrap_exceptions
from utils.win_style import set_style
from ui.sidebar import Sidebar


dpg.create_context()

_log = get_logger(__file__)
_db = Database("database/database.sqlite")
_db.migrate()


# Параметры окна
WIDTH = 800
HEIGHT = 500
TITLE_H = 30
app = {"closing": False, "state": "running"}

def on_exit():
    app["closing"] = True
    if app["state"] == "running":
        _log.info("Closing application...")
        app["state"] = "closing"
    elif app["state"] == "closing":
        _log.info("Application closed")
dpg.set_exit_callback(on_exit)

# Загружаем шрифт
font = get_font(get_current_directory(), 'roboto', italic=False)
load_font_dpg(font)


# Настройка viewport
dpg.create_viewport(title='Blitz Tools', width=WIDTH, height=HEIGHT, 
                    min_height=0, min_width=0, disable_close=True)
dpg.setup_dearpygui()
dpg.show_viewport()


# Глобальная тема + её применение
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (45, 45, 45))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (60, 60, 60))
        dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 70, 70))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 90, 90))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (110, 110, 110))
        dpg.add_theme_color(dpg.mvThemeCol_Header, (70, 70, 70))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (90, 90, 90))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (110, 110, 110))
        dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (40, 40, 40))
dpg.bind_theme(global_theme)


# Основной цикл приложения
@wrap_exceptions(logger=_log, ignore_exceptions=(Exception,))
def run_app():
    set_style()
    _log.info("App started")
    with dpg.window(tag='main_window', width=WIDTH, height=HEIGHT):
        dpg.set_primary_window('main_window', True)

        with dpg.group(horizontal=True):
            sidebar_parent = dpg.add_group(horizontal=False)

            icons_dir = get_current_directory().parent / "res" / "images"
            icon_files = [
                str(icons_dir / "settings.png"),
                str(icons_dir / "settings.png"),
                str(icons_dir / "settings.png"),
                str(icons_dir / "settings.png"),
            ]
            titles = ["Сессии", "Оленемер", "DPVL/DVPD", "Настройки"]

            for path in icon_files:
                #_log.info(f"Icon path: {path}")
                if not (icons_dir / path).exists():
                    _log.warning(f"Icon not found: {path}")

            sidebar = Sidebar(sidebar_parent, icon_files, titles)

            with dpg.child_window(width=500, height=292):
                dpg.add_text("Основная область контента. Нажимай кнопки сайдбара.")

        while dpg.is_dearpygui_running():
            if app.get("closing"):
                _db.close()
                h = dpg.get_viewport_height()
                if h > TITLE_H:
                    dpg.set_viewport_height(max(h - 5, TITLE_H))
                else:
                    break
            dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    run_app()