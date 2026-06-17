"""Enable Windows DPI awareness before creating any windows."""


def enable_dpi_awareness() -> None:
    import sys

    if sys.platform != "win32":
        return

    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
