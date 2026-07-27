__all__ = ["TankData", "NameNotSpecified", "Tankopedia"]


def __getattr__(name: str):
    if name == "TankData":
        from .data_classes import TankData

        return TankData
    if name == "NameNotSpecified":
        from .exceptions import NameNotSpecified

        return NameNotSpecified
    if name == "Tankopedia":
        from .tankopedia import Tankopedia

        return Tankopedia
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
