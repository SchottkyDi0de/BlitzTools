"""Scale dp/sp metrics from configured window size vs baseline design."""

from __future__ import annotations

from utils.window_geometry import (
    MAX_WINDOW_HEIGHT,
    MAX_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)

DESIGN_WIDTH = 800
DESIGN_HEIGHT = 500
FONT_SCALE = 1.12

_ui_scale = 1.0


def compute_ui_scale(width: int, height: int) -> float:
    if width <= 0 or height <= 0:
        return 1.0
    return min(width / DESIGN_WIDTH, height / DESIGN_HEIGHT)


def get_ui_scale() -> float:
    return _ui_scale


def apply_ui_scale(width: int, height: int) -> float:
    """Apply Kivy Metrics scale before building the widget tree."""
    global _ui_scale

    from kivy.metrics import Metrics

    width = max(MIN_WINDOW_WIDTH, min(int(width), MAX_WINDOW_WIDTH))
    height = max(MIN_WINDOW_HEIGHT, min(int(height), MAX_WINDOW_HEIGHT))
    _ui_scale = compute_ui_scale(width, height)

    base_density = getattr(Metrics, "_blitztools_base_density", None)
    base_fontscale = getattr(Metrics, "_blitztools_base_fontscale", None)
    if base_density is None:
        Metrics._blitztools_base_density = Metrics.density or 1.0
        Metrics._blitztools_base_fontscale = Metrics.fontscale or 1.0
        base_density = Metrics._blitztools_base_density
        base_fontscale = Metrics._blitztools_base_fontscale

    Metrics.density = base_density * _ui_scale
    Metrics.fontscale = base_fontscale * _ui_scale * FONT_SCALE
    return _ui_scale
