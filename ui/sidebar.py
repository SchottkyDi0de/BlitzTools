import dearpygui.dearpygui as dpg
from typing import List
import os

from ui.texture_loader import load_textures


def _on_cog_click(sender, app_data, user_data):
    print("Settings clicked")


def add_sidebar(parent: str, tag: str) -> None:
    with dpg.group(tag=tag, parent=parent, horizontal=False):
        # Загружаем текстуру
        load_textures(name='cog_btn', size=(32, 32))

        # Кнопка с изображением. Первый аргумент — тег текстуры
        dpg.add_image_button('cog_btn', width=32, height=32, callback=_on_cog_click)

        dpg.add_button(label="Copy")
        dpg.add_button(label="Paste")



SIDEBAR_WIDTH_COLLAPSED = 64
SIDEBAR_WIDTH_EXPANDED = 220
ANIMATION_STEPS = 10
ANIMATION_FRAME_DELAY = 1
ICON_SIZE = 128
BUTTON_HEIGHT = 64


class Sidebar:
    def __init__(self, parent, icons: List[str], titles: List[str]):
        assert len(icons) == len(titles)
        self.parent = parent
        self.icons = icons
        self.titles = titles
        self.count = len(icons)

        self.textures: List[int] = []
        self.groups: List[int] = []
        self.text_items: List[int] = []
        self.width_state: List[int] = []
        self.target_width: List[int] = []
        self.active_index = None
        self.animating = False

        # Загружаем текстуры
        with dpg.texture_registry(show=False):
            for path in self.icons:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Icon not found: {path}")
                w, h, channels, data = dpg.load_image(path)
                tex = dpg.add_static_texture(w, h, data)
                self.textures.append(tex)

        # Основная вертикальная группа сайдбара
        self.sidebar_group = dpg.add_group(horizontal=False, parent=self.parent)

        # Создаём кнопки
        for i in range(self.count):
            self.width_state.append(SIDEBAR_WIDTH_COLLAPSED)
            self.target_width.append(SIDEBAR_WIDTH_COLLAPSED)

            # Горизонтальная группа — контейнер для кнопки
            group = dpg.add_group(horizontal=True, parent=self.sidebar_group)
            self.groups.append(group)

            # Кнопка с иконкой
            btn = dpg.add_button(width=SIDEBAR_WIDTH_COLLAPSED,
                                 height=BUTTON_HEIGHT,
                                 parent=group,
                                 callback=self._make_onclick(i))

    def _make_onclick(self, index):
        def onclick(sender, app_data, user_data):
            if self.active_index == index:
                self.close_tab(index)
                self.active_index = None
                return
            prev = self.active_index
            self.active_index = index
            if prev is not None:
                self.close_tab(prev)
            self.open_tab(index)
        return onclick

    def open_tab(self, index):
        self.target_width[index] = SIDEBAR_WIDTH_EXPANDED
        if not self.animating:
            self.animating = True
            dpg.set_frame_callback(dpg.get_frame_count() + ANIMATION_FRAME_DELAY,
                                   lambda: self.animate_frame())

    def close_tab(self, index):
        self.target_width[index] = SIDEBAR_WIDTH_COLLAPSED
        if not self.animating:
            self.animating = True
            dpg.set_frame_callback(dpg.get_frame_count() + ANIMATION_FRAME_DELAY,
                                   lambda: self.animate_frame())

    def animate_frame(self):
        done = True
        for i, group in enumerate(self.groups):
            btn = dpg.get_item_children(group, 1)[0]  # первая (и единственная) кнопка в группе
            cur = self.width_state[i]
            tgt = self.target_width[i]

            if cur != tgt:
                done = False
                step = max(1, abs(tgt - cur)//ANIMATION_STEPS)
                cur = min(cur + step, tgt) if cur < tgt else max(cur - step, tgt)
                self.width_state[i] = cur

                dpg.configure_item(btn, width=cur)

        if not done:
            dpg.set_frame_callback(dpg.get_frame_count() + ANIMATION_FRAME_DELAY,
                                   lambda: self.animate_frame())
        else:
            self.animating = False