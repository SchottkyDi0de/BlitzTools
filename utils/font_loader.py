import dearpygui.dearpygui as dpg
from pathlib import Path

def get_font(cwd_path: Path, font_name: str, italic: bool = False) -> Path:
    return Path(cwd_path.parent) / 'res' / 'fonts' / (font_name + ('_italic' if italic else '') + '.ttf')

def load_font_dpg(font_path: Path) -> None:
    dpg.create_context()

    big_let_start = 0x00C0  # Capital "A" in cyrillic alphabet
    big_let_end = 0x00DF  # Capital "Я" in cyrillic alphabet
    remap_big_let = 0x0410  # Starting number for remapped cyrillic alphabet
    alph_len = big_let_end - big_let_start + 1  # adds the shift from big letters to small

    # Попробуем найти Arial в системной папке шрифтов Windows, иначе первый ttf как fallbac
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
                print(f'Font load error: {e}')
                default_font = None
        else:
            print("Fatal error")

    if default_font:
        dpg.bind_font(default_font)
