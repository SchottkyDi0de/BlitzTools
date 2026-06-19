from __future__ import annotations

from lib.olenemer.window.app import OlenemerApp


def toggle_windows_visibility(app: OlenemerApp) -> None:
    if not app.windows:
        return

    any_visible = any(
        window.winfo_exists() and window.winfo_ismapped()
        for window in app.windows
    )
    if any_visible:
        app.save_window_positions()
        for window in app.windows:
            if window.winfo_exists():
                window.withdraw()
        return

    for window in app.windows:
        if window.winfo_exists():
            window.deiconify()
            window.lift()
            window._ensure_topmost()


def adjust_opacity(app: OlenemerApp, delta: float, *, min_opacity: float = 0.2) -> None:
    current = float(app.olenemer_config.window_transparency)
    opacity = max(min_opacity, min(1.0, current + delta))
    if abs(opacity - current) < 1e-6:
        return

    app.set_opacity(opacity)
