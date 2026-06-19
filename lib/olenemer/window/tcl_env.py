from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_tcl_tk() -> None:
    if sys.platform != "win32":
        return

    base = Path(sys.base_prefix)
    tcl_dir = base / "tcl" / "tcl8.6"
    tk_dir = base / "tcl" / "tk8.6"

    if tcl_dir.is_dir():
        os.environ.setdefault("TCL_LIBRARY", str(tcl_dir))
    if tk_dir.is_dir():
        os.environ.setdefault("TK_LIBRARY", str(tk_dir))
