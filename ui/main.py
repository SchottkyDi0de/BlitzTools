from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

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

Builder.load_file("ui/kv/titlebar.kv")
Builder.load_file("ui/kv/screens/settings.kv")
Builder.load_file("ui/kv/screens/dvp.kv")
Builder.load_file("ui/kv/screens/replay.kv")
Builder.load_file("ui/kv/screens/cluster.kv")
Builder.load_file("ui/kv/main.kv")

class MainLayout(MDBoxLayout):
    pass
