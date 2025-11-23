import os
import glob
import dearpygui.dearpygui as dpg
from pathlib import Path

from utils.resource_path import get_resource_path, get_current_directory

def load_font_dpg(font_path):
    dpg.create_context()

    big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
    big_let_end = 0x00DF  # Capital "Я" in cyrillic alphabet
    small_let_end = 0x00FF  # small "я" in cyrillic alphabet
    remap_big_let = 0x0410  # Starting number for remapped cyrillic alphabet
    alph_len = big_let_end - big_let_start + 1  # adds the shift from big letters to small
    alph_shift = remap_big_let - big_let_start  # adds the shift from remapped to non-remapped

    # Попробуем найти Arial в системной папке шрифтов Windows, иначе первый ttf как fallback
    fonts_dir = Path(__file__).parent.parent / 'res' / 'fonts'
    preferred = os.path.join(fonts_dir, "Jost.ttf")
    font_path = None
    if os.path.exists(preferred):
        font_path = preferred
    else:
        # попробуем найти что-то похожее (может быть arialbd.ttf и т.д.)
        matches = glob.glob(os.path.join(fonts_dir, "Jost*.ttf"))
        if matches:
            font_path = matches[0]
        else:
            # крайний fallback: любой ttf в папке шрифтов
            any_ttf = glob.glob(os.path.join(fonts_dir, "*.ttf"))
            if any_ttf:
                font_path = any_ttf[0]

    default_font = None
    with dpg.font_registry():
        if font_path:
            try:
                # безопасно создать и привязать шрифт; если ошибка — пропустим
                with dpg.font(font_path, 20) as default_font:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                    biglet = remap_big_let  # Starting number for remapped cyrillic alphabet
                    for i1 in range(big_let_start, big_let_end + 1):  # Cycle through big letters in cyrillic alphabet
                        dpg.add_char_remap(i1, biglet)  # Remap the big cyrillic letter
                        dpg.add_char_remap(i1 + alph_len, biglet + alph_len)  # Remap the small cyrillic letter
                        biglet += 1  # choose next letter
            except Exception as e:
                print("Не удалось загрузить шрифт:", font_path, " — ошибка:", e)
                default_font = None
        else:
            print("Шрифт не найден в папке шрифтов Windows. Продолжаем без кастомного шрифта.")

    if default_font:
        dpg.bind_font(default_font)
