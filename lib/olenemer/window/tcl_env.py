from __future__ import annotations

import os
import sys
from pathlib import Path


def _tcl_tk_dirs() -> tuple[Path | None, Path | None]:
    if sys.platform != "win32":
        return None, None

    candidates: list[tuple[Path, Path]] = []

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        candidates.extend(
            (
                (root / "_tcl_data", root / "_tk_data"),
                (root / "tcl8.6", root / "tk8.6"),
            )
        )

    base = Path(sys.base_prefix)
    candidates.append((base / "tcl" / "tcl8.6", base / "tcl" / "tk8.6"))

    for tcl_dir, tk_dir in candidates:
        if tcl_dir.is_dir() and tk_dir.is_dir():
            return tcl_dir, tk_dir

    return None, None


def configure_tcl_tk() -> None:
    if sys.platform != "win32":
        return

    tcl_dir, tk_dir = _tcl_tk_dirs()
    if tcl_dir is not None:
        os.environ.setdefault("TCL_LIBRARY", str(tcl_dir))
    if tk_dir is not None:
        os.environ.setdefault("TK_LIBRARY", str(tk_dir))


def configure_ctk_scaling() -> None:
    """Align CTk layout units with manual pixel math used by olenemer panels."""
    if sys.platform != "win32":
        return

    from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

    ScalingTracker.deactivate_automatic_dpi_awareness = True

    import customtkinter as ctk

    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)


def prepare_olenemer_tk_env() -> None:
    configure_tcl_tk()
    configure_ctk_scaling()
