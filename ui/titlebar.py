import dearpygui.dearpygui as dpg

TITLE_BAR_HEIGHT = 30

def add_title_bar(parent_tag: str,
                  title: str,
                  width: int | None = None,
                  height: int | None = None,
                  minimize_callback=None,
                  close_callback=None,
                  tag_prefix: str = "") -> None:
    """
    Добавляет кастомный titlebar.

    - `width`: если указана, кнопки будут позиционироваться относительно этой ширины,
      иначе используется текущая ширина viewport.
    - `minimize_callback` и `close_callback`: функции, которые будут вызываться при
      нажатии на соответствующие кнопки. Если не заданы, используются стандартные
      `dpg.minimize_viewport` и `dpg.destroy_context`.
    - `tag_prefix`: префикс для tag'ов внутри titlebar (при необходимости).
    """

    base_width = width if width is not None else dpg.get_viewport_width()
    bar_height = height if height is not None else TITLE_BAR_HEIGHT

    with dpg.group(parent=parent_tag, tag=f"{tag_prefix}titlebar_group"):
        dpg.add_text(title, pos=(5, max(0, (bar_height // 2) - 8)))

        if minimize_callback is None:
            minimize_cb = lambda *_: dpg.minimize_viewport()
        else:
            minimize_cb = (lambda *_: minimize_callback()) if callable(minimize_callback) else minimize_callback

        dpg.add_button(label="_", width=30, height=20, pos=(base_width - 70, max(1, (bar_height - 20) // 2)),
                callback=minimize_cb)

        if close_callback is None:
            close_cb = lambda *_: dpg.destroy_context()
        else:
            close_cb = (lambda *_: close_callback()) if callable(close_callback) else close_callback

        dpg.add_button(label="X", width=30, height=20, pos=(base_width - 35, max(1, (bar_height - 20) // 2)),
               callback=close_cb)

    # dpg.add_spacer(parent=parent_tag)          # Функция для добавления отступа после titlebar

    registry = dpg.add_handler_registry()
    dpg.add_mouse_drag_handler(callback=lambda s, a: drag_window(a), button=0, parent=registry)

def drag_window(app_data):
    dx, dy = app_data[1], app_data[2]
    vx, vy = dpg.get_viewport_pos()
    dpg.set_viewport_pos([vx + dx, max(vy + dy, 0)])

# TODO: # 1. Добавить обработку ресайза окна (чтобы titlebar и контент подстраивались) (если мы будем делать ресайзинг)
# TODO: # 2. Добавить иконку окна в тайтлбар
# TODO: # 3. Попробовать сделать анимацию сворачивания окна, а не просто мгновенное скрытие