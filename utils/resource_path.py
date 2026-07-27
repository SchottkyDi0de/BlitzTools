from pathlib import Path
import sys


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_bundle_root() -> Path:
    """Root directory with bundled application resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return _project_root()


def get_current_directory() -> Path:
    """Backward-compatible alias for bundled resource lookup."""
    return get_bundle_root()


def get_exe_directory() -> Path:
    """Directory containing the executable when frozen, else project root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return _project_root()


def get_resource_path(relative_path: str) -> Path:
    return get_bundle_root().joinpath(relative_path)


def get_default_config_path() -> Path:
    """Bundled default config (PyInstaller _MEIPASS or dev tree)."""
    candidates = (
        get_bundle_root().joinpath("config/default_config.yaml"),
        get_exe_directory().joinpath("config/default_config.yaml"),
    )
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def _get_documents_path() -> Path:
    if sys.platform == "win32":
        try:
            from win32com.shell import shell, shellcon

            return Path(shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0))
        except Exception:
            pass
    return Path.home() / "Documents"


def get_files_path() -> Path:
    """
    Gets the absolute path to the BlitzTools folder in the user's Documents directory.

    If the folder does not exist, it is created with the necessary parent directories.

    Returns:
        Path: The absolute path to the BlitzTools folder.
    """
    path = _get_documents_path() / "BlitzTools"
    path.mkdir(parents=True, exist_ok=True)
    return path
