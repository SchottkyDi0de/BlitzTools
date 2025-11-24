import dearpygui.dearpygui as dpg

TITLE_BAR_HEIGHT = 30
can_drag = False

def add_title_bar(parent_tag: str,
                  title: str,
                  width: int | None = None,
                  bar_width: int | None = 500,
                  bar_height: int | None = 30,
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
    global can_drag

    titlebar_tag = f"{tag_prefix}titlebar_area"

    # ВАЖНО: создаём невидимую область-тайтлбар
    dpg.add_child_window(
        tag=titlebar_tag,
        parent=parent_tag,
        width=bar_width,
        height=bar_height,
        no_scrollbar=True,
        border=False
    )

    # --- надпись ---
    dpg.add_text(title, pos=(5, (bar_height // 2) - 8), parent=titlebar_tag)

    # --- кнопки ---
    if minimize_callback is None:
        minimize_callback = lambda *_: dpg.minimize_viewport()

    if close_callback is None:
        close_callback = lambda *_: dpg.destroy_context()

    dpg.add_button(label="_", width=30, height=20,
                   pos=(bar_width - 70, (bar_height - 20) // 2),
                   parent=titlebar_tag,
                   callback=minimize_callback)

    dpg.add_button(label="X", width=30, height=20,
                   pos=(bar_width - 35, (bar_height - 20) // 2),
                   parent=titlebar_tag,
                   callback=close_callback)

    # --- мышиные события ---
    reg = dpg.add_handler_registry()

    # при нажатии определяем: нажали ли по тайтлбару
    dpg.add_mouse_down_handler(callback=lambda s,a: check_titlebar_click(titlebar_tag), parent=reg)

    # перетаскиваем только если разрешено
    dpg.add_mouse_drag_handler(callback=lambda s,a: drag_window(a), button=0, parent=reg)

    # при отпускании прекращаем перетаскивание
    dpg.add_mouse_release_handler(callback=lambda: stop_drag(), parent=reg)


def check_titlebar_click(titlebar_tag):
    """Определяет, было ли нажатие внутри тайтлбара."""
    global can_drag

    mx, my = dpg.get_mouse_pos()

    # координаты тайтлбара в окне
    x, y = dpg.get_item_pos(titlebar_tag)
    w = dpg.get_item_width(titlebar_tag)
    h = dpg.get_item_height(titlebar_tag)

    print(f"\rTitlebar pos: ({x}, {y}), size: ({w}, {h}), mouse: ({mx}, {my})", end="")
    if x <= mx <= x + w and y <= my <= y + h:
        can_drag = True

def drag_window(app_data):
    """Перемещение окна, если разрешено."""
    global can_drag
    if not can_drag:
        return

    dx, dy = app_data[1], app_data[2]
    vx, vy = dpg.get_viewport_pos()

    dpg.set_viewport_pos([vx + dx, vy + dy])

def stop_drag():
    """Запрещаем перетаскивание при отпускании мыши."""
    global can_drag
    can_drag = False

# TODO: # 1. Добавить обработку ресайза окна (чтобы titlebar и контент подстраивались) (если мы будем делать ресайзинг)
# TODO: # 2. Добавить иконку окна в тайтлбар
# TODO: # 3. Попробовать сделать анимацию сворачивания окна, а не просто мгновенное скрытие