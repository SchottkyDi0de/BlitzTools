import dearpygui.dearpygui as dpg
from ui.texture_loader import load_textures


def _on_cog_click(sender, app_data, user_data):
    print("Settings clicked")


def add_sidebar(parent: str, tag: str) -> None:
    with dpg.group(tag=tag, parent=parent):
        # Загружаем текстуру
        load_textures(name='cog_btn', size=(32, 32))

        # Кнопка с изображением. Первый аргумент — тег текстуры
        dpg.add_image_button('cog_btn', width=32, height=32, callback=_on_cog_click)
        dpg.add_same_line()
        dpg.add_text("Settings")

        dpg.add_button(label="Copy")
        dpg.add_button(label="Paste")
