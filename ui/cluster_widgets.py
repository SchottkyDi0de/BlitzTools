from __future__ import annotations

from ui.widgets import SettingsOptionButton


class ClusterSelectButton(SettingsOptionButton):
    blocked = False

    def sync_appearance(self):
        if not getattr(self, "canvas", None):
            return
        super().sync_appearance()
        self._sync_option_label_color()
