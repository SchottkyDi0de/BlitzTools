from __future__ import annotations

import platform
from pathlib import Path


def _build_filter_pipe(filetypes: list[tuple[str, str]] | None) -> str:
    pairs = filetypes or [("All files", "*.*")]
    parts: list[str] = []
    for label, pattern in pairs:
        parts.extend([f"{label} ({pattern})", pattern])
    parts.append("")
    return "|".join(parts)


def _parse_multiselect(raw: str) -> list[str]:
    if not raw:
        return []
    if "\0" not in raw:
        return [raw]

    parts = [part for part in raw.split("\0") if part]
    if len(parts) == 1:
        return parts

    folder, *files = parts
    if not files:
        return [folder]
    return [str(Path(folder) / name) for name in files]


def _pick_files_win32(
    *,
    title: str = "",
    filetypes: list[tuple[str, str]] | None = None,
) -> list[str]:
    import win32con
    import win32ui

    flags = (
        win32con.OFN_ALLOWMULTISELECT
        | win32con.OFN_EXPLORER
        | win32con.OFN_FILEMUSTEXIST
        | win32con.OFN_PATHMUSTEXIST
    )
    dlg = win32ui.CreateFileDialog(
        1,
        None,
        None,
        flags,
        _build_filter_pipe(filetypes),
    )
    if title:
        dlg.SetOFNTitle(title)

    if dlg.DoModal() != 1:
        return []

    if hasattr(dlg, "GetPathNames"):
        names = dlg.GetPathNames()
        if isinstance(names, (list, tuple)):
            return [str(path) for path in names if path]
        if names:
            return _parse_multiselect(str(names))

    return _parse_multiselect(dlg.GetPathName())


def _pick_folder_win32(*, title: str = "") -> str | None:
    try:
        return _pick_folder_win32_modern(title=title)
    except OSError:
        return None


def _com_hresult(func, *args):
    """Call a COM vtable method; treat cancel as HRESULT instead of raising."""
    try:
        return func(*args)
    except OSError as exc:
        if exc.winerror is not None:
            return exc.winerror
        raise


def _hresult_failed(hr: int) -> bool:
    return hr < 0


def _win32_foreground_hwnd():
    import ctypes

    return ctypes.windll.user32.GetForegroundWindow()


def _com_guid(guid_string: str):
    import ctypes
    import ctypes.wintypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    guid = GUID()
    ctypes.windll.ole32.CLSIDFromString(
        ctypes.wintypes.LPCWSTR(guid_string),
        ctypes.byref(guid),
    )
    return guid


def _com_release(ptr) -> None:
    import ctypes

    if not ptr:
        return
    vtable = ctypes.cast(
        ctypes.cast(ptr, ctypes.POINTER(ctypes.c_void_p))[0],
        ctypes.POINTER(ctypes.c_void_p * 3),
    ).contents
    Release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
    Release(ptr)


def _pick_folder_win32_modern(*, title: str = "") -> str | None:
    """Explorer-style folder picker (same UI family as the open-file dialog)."""
    import ctypes
    import ctypes.wintypes

    CLSID_FileOpenDialog = _com_guid("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
    IID_IFileOpenDialog = _com_guid("{D57C7288-D4AD-4768-BE02-9D969532D960}")

    FOS_PICKFOLDERS = 0x00000020
    FOS_FORCEFILESYSTEM = 0x00000040
    FOS_NOCHANGEDIR = 0x00000008
    FOS_PATHMUSTEXIST = 0x00000800

    ole32 = ctypes.windll.ole32
    try:
        import pythoncom

        pythoncom.CoInitialize()
    except Exception:
        ole32.CoInitialize(None)

    p_dialog = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        ctypes.byref(CLSID_FileOpenDialog),
        None,
        1,
        ctypes.byref(IID_IFileOpenDialog),
        ctypes.byref(p_dialog),
    )
    if hr != 0:
        raise OSError(hr, "CoCreateInstance(FileOpenDialog) failed", None, hr)

    vtable = ctypes.cast(
        ctypes.cast(p_dialog, ctypes.POINTER(ctypes.c_void_p))[0],
        ctypes.POINTER(ctypes.c_void_p * 28),
    ).contents

    try:
        GetOptions = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)
        )(vtable[10])
        SetOptions = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.c_uint
        )(vtable[9])

        opts = ctypes.c_uint()
        hr = _com_hresult(GetOptions, p_dialog, ctypes.byref(opts))
        if _hresult_failed(hr):
            return None
        hr = _com_hresult(
            SetOptions,
            p_dialog,
            opts.value
            | FOS_PICKFOLDERS
            | FOS_FORCEFILESYSTEM
            | FOS_NOCHANGEDIR
            | FOS_PATHMUSTEXIST,
        )
        if _hresult_failed(hr):
            return None

        if title:
            SetTitle = ctypes.WINFUNCTYPE(
                ctypes.HRESULT, ctypes.c_void_p, ctypes.wintypes.LPCWSTR
            )(vtable[17])
            hr = _com_hresult(SetTitle, p_dialog, title)
            if _hresult_failed(hr):
                return None

        Show = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.wintypes.HWND
        )(vtable[3])
        hr = _com_hresult(Show, p_dialog, _win32_foreground_hwnd())
        if hr != 0:
            return None

        GetResult = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
        )(vtable[20])
        p_item = ctypes.c_void_p()
        hr = _com_hresult(GetResult, p_dialog, ctypes.byref(p_item))
        if _hresult_failed(hr) or not p_item:
            return None

        try:
            item_vtable = ctypes.cast(
                ctypes.cast(p_item, ctypes.POINTER(ctypes.c_void_p))[0],
                ctypes.POINTER(ctypes.c_void_p * 6),
            ).contents
            GetDisplayName = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.POINTER(ctypes.wintypes.LPWSTR),
            )(item_vtable[5])

            path_ptr = ctypes.wintypes.LPWSTR()
            hr = _com_hresult(GetDisplayName, p_item, 0x80058000, ctypes.byref(path_ptr))
            if _hresult_failed(hr) or not path_ptr:
                return None
            path = path_ptr.value
            ole32.CoTaskMemFree(path_ptr)
            return path or None
        finally:
            _com_release(p_item)
    finally:
        _com_release(p_dialog)


def pick_files(*, title: str = "", filetypes: list[tuple[str, str]] | None = None) -> list[str]:
    if platform.system() == "Windows":
        return _pick_files_win32(title=title, filetypes=filetypes)

    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        paths = filedialog.askopenfilenames(
            title=title,
            filetypes=filetypes or [("All files", "*.*")],
        )
    finally:
        root.destroy()

    return list(paths)


def pick_folder(*, title: str = "") -> str | None:
    if platform.system() == "Windows":
        return _pick_folder_win32(title=title)

    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = filedialog.askdirectory(title=title, mustexist=True)
    finally:
        root.destroy()

    return path or None
