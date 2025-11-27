import dearpygui.dearpygui as dpg
from PIL import Image

from utils.resource_path import get_resource_path

def load_textures(name: str, size: tuple[int, int] | None = None) -> None:
    print(get_resource_path(f"images/{name}.png"))
    width, height, _, data = dpg.load_image(f'{get_resource_path(f"res/images/{name}.png")}')
    
    with dpg.texture_registry():
        dpg.add_static_texture(width, height, data, tag=name)
