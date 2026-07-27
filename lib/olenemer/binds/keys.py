from __future__ import annotations

from pynput.keyboard import Key


def parse_keybind(name: str) -> Key | None:
    normalized = name.strip().upper().replace("_", "")
    if normalized.startswith("F") and normalized[1:].isdigit():
        return getattr(Key, normalized.lower(), None)

    aliases = {
        "SPACE": Key.space,
        "ENTER": Key.enter,
        "ESC": Key.esc,
        "ESCAPE": Key.esc,
        "TAB": Key.tab,
        "PAGEUP": Key.page_up,
        "PAGEDOWN": Key.page_down,
        "HOME": Key.home,
        "END": Key.end,
        "INSERT": Key.insert,
        "DELETE": Key.delete,
    }
    return aliases.get(normalized)
