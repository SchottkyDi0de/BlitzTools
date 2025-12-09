import platform
import ctypes
import threading


if platform.system() == "Windows" and int(platform.release()) >= 10:
    from hPyT import title_bar_color
    import winaccent


_HWND = None

class ApperanceHundler:
    pass