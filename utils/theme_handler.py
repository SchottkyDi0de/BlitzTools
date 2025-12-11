import ctypes
import threading


class ThemeHandler:
    def __init__(self, window):
        self.HWND = ctypes.windll.kernel32.GetForegroundWindow()