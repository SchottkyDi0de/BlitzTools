from __future__ import annotations

_FRAME_RULES: tuple[tuple[str, tuple[float, float, float, float]], ...] = (
    ("legend", (1.0, 0.72, 0.15, 1.0)),
    ("gold", (1.0, 0.78, 0.2, 1.0)),
    ("unique", (0.62, 0.35, 0.95, 1.0)),
    ("epic", (0.62, 0.35, 0.95, 1.0)),
    ("rare", (0.25, 0.62, 1.0, 1.0)),
    ("blue", (0.25, 0.62, 1.0, 1.0)),
    ("common", (0.55, 0.58, 0.64, 1.0)),
    ("default", (0.45, 0.48, 0.52, 1.0)),
)


def frame_color_for_kind(kind: str, palette: dict | None = None) -> tuple[float, float, float, float]:
    normalized = (kind or "").lower()
    for token, color in _FRAME_RULES:
        if token in normalized:
            return color
    if palette:
        accent = palette.get("accent", (0, 0.94, 1, 1))
        dim = palette.get("accent_dim", accent)
        return tuple(dim[:4]) if len(dim) >= 4 else (0.45, 0.48, 0.52, 1.0)
    return (0.45, 0.48, 0.52, 1.0)
