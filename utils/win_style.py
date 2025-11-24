from ctypes import windll, c_int, byref

from pywinstyles.py_win_style import ChangeDWMAttrib, ChangeDWMAccent, ExtendFrameIntoClientArea


def set_style(style: str = "acrylic"):
    if style == "acrylic":
        hwnd = windll.user32.GetActiveWindow()

        ChangeDWMAttrib(hwnd, 20, c_int(1))
        ChangeDWMAccent(hwnd, 30, 3, color=0x292929)
        ExtendFrameIntoClientArea(hwnd)
