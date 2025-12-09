from pathlib import Path
import os
import sys


def get_resource_path(relative_path: str) -> Path:
    """
    Gets the absolute path to a resource, either from the root of the source
    directory or from the root of the application if the script is frozen.

    Args:
        relative_path (str): The relative path to the resource.

    Returns:
        Path: The absolute path to the resource.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        application_path = Path(sys._MEIPASS) # type: ignore
    else:
        application_path = Path(os.getcwd())

    return Path(application_path).joinpath(relative_path)


def get_current_directory() -> Path:
    """
    Gets the absolute path to the current directory.

    If the script is frozen, this returns the absolute path to the directory
    of the executable. Otherwise, this returns the absolute path to the
    directory of the script.

    Returns:
        Path: The absolute path to the current directory.
    """
    if getattr(sys, 'frozen', False):
        application_path = Path(os.path.dirname(sys.executable))
    elif __file__:
        application_path = Path(os.path.dirname(__file__)).parent

    return application_path

def get_files_path() -> Path:
    """
    Gets the absolute path to the BlitzTools folder in the user's Documents directory.

    If the folder does not exist, it is created with the necessary parent directories.

    Returns:
        Path: The absolute path to the BlitzTools folder.
    """
    path = Path('~').expanduser() / 'Documents' /'BlitzTools'
    if not path.exists():
        path.mkdir(parents=True)
        
    return path
