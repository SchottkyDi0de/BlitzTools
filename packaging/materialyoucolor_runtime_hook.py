"""PyInstaller runtime hook: avoid loading materialyoucolor celebi .pyd in frozen builds.

The native celebi extension segfaults when imported from PyInstaller onefile on
Windows. KivyMD only needs materialyoucolor for theming; wallpaper quantization
is optional and unused on desktop.
"""

import sys
from types import ModuleType

if getattr(sys, "frozen", False):
    celebi_module = ModuleType("materialyoucolor.quantize.celebi")
    quantize_module = ModuleType("materialyoucolor.quantize")
    quantize_module.ImageQuantizeCelebi = None
    quantize_module.QuantizeCelebi = None
    sys.modules["materialyoucolor.quantize.celebi"] = celebi_module
    sys.modules["materialyoucolor.quantize"] = quantize_module
