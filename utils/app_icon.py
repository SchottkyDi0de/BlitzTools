from __future__ import annotations

import platform
import sys
from pathlib import Path

from utils.resource_path import get_resource_path

_ICON_STEM = "images/icon"


def icon_path(ext: str = "ico") -> Path:
    normalized = ext.lower().lstrip(".")
    return get_resource_path(f"{_ICON_STEM}.{normalized}")


def icon_path_str(ext: str = "ico") -> str:
    return str(icon_path(ext).resolve())


def apply_tk_window_icon(window) -> None:
    ico = icon_path("ico")
    if not ico.is_file():
        return

    try:
        window.iconbitmap(default=icon_path_str("ico"))
        return
    except Exception:
        pass

    png = icon_path("png")
    if not png.is_file():
        return

    try:
        import tkinter as tk

        photo = tk.PhotoImage(file=icon_path_str("png"))
        window.iconphoto(True, photo)
        window._blitztools_icon_photo = photo
    except Exception:
        pass


def apply_win32_hwnd_icon(hwnd: int | None = None) -> bool:
    if platform.system() != "Windows":
        return False

    from ctypes import windll

    ico = icon_path("ico")
    if not ico.is_file():
        return False

    if hwnd is None:
        hwnd = int(windll.user32.GetActiveWindow())
    if not hwnd:
        return False

    WM_SETICON = 0x80
    ICON_SMALL = 0
    ICON_BIG = 1
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x10
    LR_DEFAULTSIZE = 0x40

    hicon = windll.user32.LoadImageW(
        None,
        icon_path_str("ico"),
        IMAGE_ICON,
        0,
        0,
        LR_LOADFROMFILE | LR_DEFAULTSIZE,
    )
    if not hicon:
        return False

    windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
    return True


def apply_kivy_app_icon(app=None) -> None:
    try:
        from kivy.core.window import Window
        from kivymd.app import MDApp
    except ImportError:
        return

    if app is None:
        app = MDApp.get_running_app()
    if app is None:
        return

    if not app.icon:
        app.icon = "images/icon.png"

    icon = app.get_application_icon() if hasattr(app, "get_application_icon") else ""
    if icon:
        Window.set_icon(icon)

    apply_win32_hwnd_icon()


def apply_kivy_window_icon() -> None:
    if platform.system() != "Windows":
        return

    try:
        from kivy.clock import Clock
        from kivymd.app import MDApp
    except ImportError:
        return

    app = MDApp.get_running_app()

    def _apply(_dt):
        apply_kivy_app_icon(app)

    Clock.schedule_once(_apply, 0)
    Clock.schedule_once(_apply, 0.2)


def apply_frozen_process_icon() -> None:
    if platform.system() != "Windows" or not getattr(sys, "frozen", False):
        return
    apply_win32_hwnd_icon()
