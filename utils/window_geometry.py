MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300


def is_valid_window_size(width: int, height: int) -> bool:
    return width >= MIN_WINDOW_WIDTH and height >= MIN_WINDOW_HEIGHT


def sanitize_window_config(window, default_window) -> bool:
    """Fix invalid window geometry in-place. Returns True if anything changed."""
    changed = False

    if not is_valid_window_size(window.width, window.height):
        window.width = default_window.width
        window.height = default_window.height
        changed = True

    if window.pos is None or len(window.pos) != 2:
        window.pos = list(default_window.pos)
        changed = True

    return changed
