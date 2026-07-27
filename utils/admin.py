import platform

_elevated: bool | None = None


def is_elevated() -> bool:
    """True when the current Windows process has admin privileges."""
    global _elevated
    if _elevated is not None:
        return _elevated

    if platform.system() != "Windows":
        _elevated = False
        return False

    try:
        import ctypes

        _elevated = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        _elevated = False
    return _elevated


def needs_admin_notice() -> bool:
    """True on Windows when the process is not elevated."""
    return platform.system() == "Windows" and not is_elevated()
