from __future__ import annotations

from ctypes import WINFUNCTYPE, POINTER, Structure, byref, c_bool, c_long, c_ulong, sizeof, windll
from ctypes.wintypes import DWORD, RECT

MAGNET_THRESHOLD = 20


class MONITORINFO(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
    ]


def get_monitors() -> list[dict[str, int]]:
    monitors: list[dict[str, int]] = []

    def _callback(_hmon, _hdc, _lprect, _data):
        info = MONITORINFO()
        info.cbSize = sizeof(MONITORINFO)
        if windll.user32.GetMonitorInfoW(_hmon, byref(info)):
            rect = info.rcMonitor
            monitors.append(
                {
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                }
            )
        return True

    enum_proc = WINFUNCTYPE(c_bool, c_ulong, c_ulong, POINTER(RECT), c_long)(_callback)
    windll.user32.EnumDisplayMonitors(0, None, enum_proc, 0)
    return monitors or [{"x": 0, "y": 0, "width": 1920, "height": 1080}]


def get_monitor_at(x: int, y: int) -> dict[str, int]:
    for monitor in get_monitors():
        if monitor["x"] <= x <= monitor["x"] + monitor["width"] and monitor["y"] <= y <= monitor["y"] + monitor["height"]:
            return monitor
    return get_monitors()[0]
