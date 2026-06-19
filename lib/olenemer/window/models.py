from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlayerRowData:
    nickname: str
    clan_tag: str | None
    platoon_index: int
    avatar_url: str
    frame_kind: str
    profile_skin_url: str
    tank_level: int
    tank_category: str
    tank_name: str
    marks: int
    battles: int
    winrate: float
    avg_damage: int
    rating: int
    calibrated: bool
    is_author: bool
    author_clan_tag: str | None


@dataclass
class TeamViewData:
    title: str
    rows: list[PlayerRowData] = field(default_factory=list)
    summary_battles: float = 0.0
    summary_winrate: float = 0.0
    summary_damage: float = 0.0
    summary_rating: float = 0.0
