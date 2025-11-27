import dearpygui.dearpygui as dpg
from ui.texture_loader import load_texture


# load_texture('cog_btn')
def add_sidebar(parent: str, tag: str) -> None:
    with dpg.group(tag=tag, parent=parent):
        # dpg.add_image_button(tex="cog_btn", label="Settings")
        dpg.add_button(label="Copy")
        dpg.add_button(label="Paste")
