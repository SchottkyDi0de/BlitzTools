# Импорты библиотек
import pywinstyles
from ctypes import windll
from pathlib import Path

import dearpygui.dearpygui as dpg

# Импорты из проекта
from utils.resource_path import get_current_directory
from utils.font_loader import get_font, load_font_dpg
from utils.logger import get_logger

_log = get_logger(__file__)


# Параметры окна
WIDTH = 800
HEIGHT = 500
TITLE_H = 30
app_state = {"closing": False}

# Функции для кнопок titlebar
def do_minimize(): dpg.minimize_viewport()
def do_close(): app_state["closing"] = True

# Создаём контекст и загружаем шрифт
dpg.create_context()
font = get_font(get_current_directory(), 'roboto', italic=False)
load_font_dpg(font)


with dpg.window(tag="main_win", no_title_bar=True, no_resize=True,
                no_move=True, width=WIDTH, height=HEIGHT, pos=(0, 0),
                menubar=False, no_scrollbar=True):

    # Контент (таблица)
    with dpg.group(tag="content"):
        with dpg.table(header_row=True, resizable=True, policy=dpg.mvTable_SizingStretchProp,
                        borders_innerH=True, borders_outerH=True, borders_innerV=True,
                        borders_outerV=True, row_background=True, no_host_extendX=True,
                        hideable=True, reorderable=True, sortable=True):
            dpg.add_table_column()
            dpg.add_table_column()
            dpg.add_table_column()

            for i in range(5):
                with dpg.table_row():
                    dpg.add_text(f"Строка {i} Данные 1 !@##$$%%^")
                    dpg.add_text(f"Строка {i} Данные 2")
                    dpg.add_text(f"Строка {i} Данные 3")


# Настройка viewport
dpg.create_viewport(title='DearPyGui Demo', width=WIDTH, height=HEIGHT)

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

# Показ viewport
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main_win", True)
hwnd = windll.user32.GetActiveWindow()
pywinstyles.apply_style(hwnd, "acrylic")
_log.info("App started")
# Главный цикл с анимацией закрытия
while dpg.is_dearpygui_running():
    if app_state.get("closing"):
        h = dpg.get_viewport_height()
        if h > TITLE_H:
            dpg.set_viewport_height(max(h - 5, TITLE_H))
        else:
            break
    dpg.render_dearpygui_frame()

# Очистка контекста
dpg.destroy_context()