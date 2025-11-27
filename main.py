# Импорты библиотек
import pywinstyles
from ctypes import windll
from pathlib import Path

import dearpygui.dearpygui as dpg

# Импорты из проекта
from utils.resource_path import get_current_directory
from utils.font_loader import get_font, load_font_dpg
from utils.logger import get_logger
from lib.db.database import Database
from utils.exc_wrapper import wrap_exceptions

from ui.sidebar import add_sidebar


dpg.create_context()

_log = get_logger(__file__)
_db = Database("database/database.sqlite")
_db.migrate()

# Параметры окна
WIDTH = 800
HEIGHT = 500
TITLE_H = 30
app_state = {"closing": False}


# загружаем шрифт
font = get_font(get_current_directory(), 'roboto', italic=False)
load_font_dpg(font)


# Настройка viewport
dpg.create_viewport(title='Blitz Tools', width=WIDTH, height=HEIGHT)

dpg.setup_dearpygui()
dpg.show_viewport()
# dpg.set_primary_window("main_win", True)

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


hwnd = windll.user32.GetActiveWindow()
pywinstyles.apply_style(hwnd, "acrylic")
_log.info("App started")

@wrap_exceptions(logger=_log, ignore_exceptions=(Exception,))
def run_app():
    with dpg.window(tag='main_window', width=WIDTH, height=HEIGHT):
        dpg.set_primary_window('main_window', True)
        
        add_sidebar("main_window", 'bar')
        while dpg.is_dearpygui_running():
            if app_state.get("closing"):
                _db.close()
                h = dpg.get_viewport_height()
                if h > TITLE_H:
                    dpg.set_viewport_height(max(h - 5, TITLE_H))
                else:
                    break
            dpg.render_dearpygui_frame()
            
        

    dpg.destroy_context()
    
run_app()