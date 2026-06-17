from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from utils.resource_path import get_resource_path

from ui.cluster_screen import ClusterScreen  # noqa: F401
from ui.dvp_screen import DvpScreen  # noqa: F401
from ui.replay_screen import ReplayScreen  # noqa: F401
from ui.settings_screen import SettingsScreen  # noqa: F401
from ui.cluster_widgets import ClusterSelectButton  # noqa: F401
from ui.replay_widgets import ReplayAvatar, ReplayPlayerRow, ReplayTeamPanel, ReplayTankCell, TankMarksIndicator, TopAlignedHBox  # noqa: F401
from ui.widgets import (  # noqa: F401
    AdminNoticeBar,
    AdminNoticeDismissButton,
    CustomTitleBar,
    DvpActionButton,
    FuturaFeatureCard,
    FuturaNavButton,
    PassThroughLabel,
    PassThroughHint,
    PlaceholderPane,
    SettingsOptionButton,
    StatusDot,
    ThemeToggleButton,
    TitleBarButton,
)

_KV_FILES = (
    "ui/kv/titlebar.kv",
    "ui/kv/screens/settings.kv",
    "ui/kv/screens/dvp.kv",
    "ui/kv/screens/replay.kv",
    "ui/kv/screens/cluster.kv",
    "ui/kv/main.kv",
)

for _kv_file in _KV_FILES:
    Builder.load_file(str(get_resource_path(_kv_file)))

class MainLayout(MDBoxLayout):
    pass
