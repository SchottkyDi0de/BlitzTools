MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300

LEGACY_DEFAULT_WIDTH = 800
LEGACY_DEFAULT_HEIGHT = 500


def is_valid_window_size(width: int, height: int) -> bool:
    return width >= MIN_WINDOW_WIDTH and height >= MIN_WINDOW_HEIGHT


def migrate_legacy_window_size(window, default_window) -> bool:
    """Upgrade untouched legacy 800x500 window size to current defaults."""
    if (
        window.width == LEGACY_DEFAULT_WIDTH
        and window.height == LEGACY_DEFAULT_HEIGHT
        and (
            default_window.width != LEGACY_DEFAULT_WIDTH
            or default_window.height != LEGACY_DEFAULT_HEIGHT
        )
    ):
        window.width = default_window.width
        window.height = default_window.height
        return True
    return False


def migrate_legacy_window_size_dict(window: dict, default_window: dict) -> bool:
    width = int(window.get("width", 0))
    height = int(window.get("height", 0))
    default_w = int(default_window["width"])
    default_h = int(default_window["height"])
    if (
        width == LEGACY_DEFAULT_WIDTH
        and height == LEGACY_DEFAULT_HEIGHT
        and (default_w, default_h) != (LEGACY_DEFAULT_WIDTH, LEGACY_DEFAULT_HEIGHT)
    ):
        window["width"] = default_w
        window["height"] = default_h
        return True
    return False


def migrate_legacy_olenemer_positions(config, default_config) -> bool:
    changed = False
    olenemer = getattr(config, "olenemer", None)
    if olenemer is None:
        return False

    default_width = default_config.app_global.window.width
    right = olenemer.window_pos_right
    if (
        isinstance(right, list)
        and len(right) == 2
        and right[1] == 0
        and right[0] == LEGACY_DEFAULT_WIDTH
        and default_width != LEGACY_DEFAULT_WIDTH
    ):
        olenemer.window_pos_right = [default_width, 0]
        changed = True
    return changed


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


def migrate_window_config(config, default_config) -> bool:
    changed = False
    if migrate_legacy_window_size(config.app_global.window, default_config.app_global.window):
        changed = True
    if migrate_legacy_olenemer_positions(config, default_config):
        changed = True
    return changed
