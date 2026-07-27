from enum import StrEnum
from pathlib import Path


class Region(StrEnum):
    RU: str = "ru"
    EU: str = "eu"


def region_from_filename(path: str | Path) -> Region:
    """EU client replays use .wotbreplay; Lesta/RU replays use .tbreplay."""
    suffix = Path(path).suffix.lower()
    if suffix == ".wotbreplay":
        return Region.EU
    if suffix == ".tbreplay":
        return Region.RU
    return Region.RU