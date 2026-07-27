"""Windows display scale helpers for consistent window geometry in config."""

from __future__ import annotations

import sys


def get_windows_scale_factor(hwnd: int | None = None) -> float:
    """Return effective UI scale (1.0 = 100%, 1.25 = 125%)."""
    if sys.platform != "win32":
        return 1.0

    try:
        import ctypes

        user32 = ctypes.windll.user32
        if hwnd:
            dpi = user32.GetDpiForWindow(hwnd)
            if dpi > 0:
                return dpi / 96.0

        try:
            dpi = user32.GetDpiForSystem()
            if dpi > 0:
                return dpi / 96.0
        except Exception:
            pass

        hdc = user32.GetDC(0)
        try:
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            if dpi > 0:
                return dpi / 96.0
        finally:
            user32.ReleaseDC(0, hdc)
    except Exception:
        return 1.0

    return 1.0


def to_logical_pixels(value: int, hwnd: int | None = None) -> int:
    """Convert reported window pixels to 96-DPI logical units for config storage."""
    scale = get_windows_scale_factor(hwnd)
    if scale <= 1.0:
        return int(value)
    return max(1, round(value / scale))


def from_logical_pixels(value: int, hwnd: int | None = None) -> int:
    """Convert config logical units to pixels for native APIs when needed."""
    return max(1, round(value * get_windows_scale_factor(hwnd)))
