from pathlib import Path

from utils.resource_path import get_current_directory
from kivy.resources import resource_add_path, resource_find


def add_assets() -> None:
    """
    Adds the 'res' directory as a resource path.

    This function should be called before any other resource-related functions
    to ensure that the resources are properly loaded.

    The 'res' directory should contain all the assets for the application, such
    as images, fonts, and other media.
    """
    resource_path = get_current_directory().joinpath('res')
    resource_add_path(resource_path)
    resource_add_path(resource_path.joinpath('fonts'))

def get_available_fonts() -> dict[str, str]:
    """
    Returns a dictionary of available fonts, where the key is the font name
    without the extension and the value is the full path to the font file.

    Returns:
        dict[str, str]: A dictionary of available fonts.
    """
    font_path = resource_find('fonts')
    return {f.stem: str(f) for f in Path(font_path).iterdir() if f.suffix == '.ttf'}

def get_font(font_name: str) -> str:
    """
    Returns the full path to the font file with the given name.

    Args:
        font_name (str): The name of the font without the extension.

    Returns:
        Path: The full path to the font file.
    """
    return resource_find(f'fonts/{font_name}.ttf')
