"""PyInstaller runtime hook: enable DPI awareness before Kivy/SDL start."""

import sys

if sys.platform == "win32":
    try:
        import ctypes

        # PROCESS_PER_MONITOR_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
