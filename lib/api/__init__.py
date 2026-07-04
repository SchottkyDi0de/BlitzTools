__all__ = ["BlitzAPI"]


def __getattr__(name: str):
    if name == "BlitzAPI":
        from .api import BlitzAPI

        return BlitzAPI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
