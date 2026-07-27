from __future__ import annotations

from zipfile import ZipFile
from dataclasses import dataclass, field
from datetime import datetime, timezone

from lib.replay_parser.marks import decode_marks_value
from lib.replay_parser.models.enums import RoomType, TeamNumber
from lib.replay_parser.models.meta import Meta
from lib.replay_parser.models.region import Region, region_from_filename
from lib.replay_parser.replay import Replay
from lib.replay_parser.types import BattleResults, Player
from lib.tankopedia import Tankopedia


@dataclass
class PlayerRow:
    account_id: int
    nickname: str
    clan_tag: str
    avatar_url: str
    frame_kind: str
    tank_id: int
    tank_label: str
    damage: int
    kills: int
    blocked: int
    xp: int
    credits: int
    marks: int
    hits: int
    penetrations: int
    mm_rating: float | None
    platoon_id: int | None


@dataclass
class ReplayBattleView:
    recorder_name: str
    map_id: int
    duration_secs: float
    battle_time: datetime | None
    room_type_label: str
    winner_team: int | None
    author_account_id: int = 0
    author_xp: int = 0
    author_credits: int = 0
    author_damage: int = 0
    free_xp: int = 0
    author_tank_label: str = "—"
    author_marks: int = 0
    team1: list[PlayerRow] = field(default_factory=list)
    team2: list[PlayerRow] = field(default_factory=list)


def parse_replay_file(
    path: str,
    region: Region | None = None,
    *,
    language: str = "ru",
) -> ReplayBattleView:
    parse_region = region or region_from_filename(path)
    with ZipFile(path, "r") as handle:
        with Replay.open(handle, parse_region) as replay:
            meta = replay.read_meta()
            results = replay.read_battle_results()
    tankopedia_region = region_from_filename(path)
    return build_battle_view(
        meta,
        results,
        region=parse_region,
        tankopedia_region=tankopedia_region,
        language=language,
    )


def build_battle_view(
    meta: Meta,
    results: BattleResults,
    *,
    region: Region,
    tankopedia_region: Region | None = None,
    language: str = "ru",
) -> ReplayBattleView:
    tank_region = tankopedia_region or region
    tankopedia = Tankopedia("ru" if tank_region == Region.RU else "eu")
    results_by_account = {
        item.info.account_id: item.info for item in results.player_results
    }

    team1: list[PlayerRow] = []
    team2: list[PlayerRow] = []
    for player in results.players:
        row = _build_player_row(player, results_by_account, tankopedia, language)
        if player.info.team == TeamNumber.ONE:
            team1.append(row)
        elif player.info.team == TeamNumber.TWO:
            team2.append(row)

    team1.sort(key=lambda row: row.damage, reverse=True)
    team2.sort(key=lambda row: row.damage, reverse=True)

    winner = int(results.winner_team_number) if results.winner_team_number else None
    battle_time = None
    if results.timestamp_secs:
        battle_time = datetime.fromtimestamp(results.timestamp_secs, tz=timezone.utc)

    author = results.author
    author_account_id = int(author.account_id or 0)
    author_marks = 0
    for player in results.players:
        if int(player.account_id) == author_account_id:
            author_marks = decode_marks_value(getattr(player.info, "marks", None))
            break

    return ReplayBattleView(
        recorder_name=meta.player_name,
        map_id=int(meta.map_id),
        duration_secs=meta.battle_duration_secs,
        battle_time=battle_time,
        room_type_label=_room_type_label(RoomType(results.room_type)),
        winner_team=winner,
        author_account_id=author_account_id,
        author_xp=int(author.total_xp or 0),
        author_credits=int(author.total_credits or 0),
        author_damage=int(author.damage_dealt or 0),
        free_xp=int(results.free_xp or 0),
        author_tank_label=_tank_label(tankopedia, int(meta.tank_id or 0), language),
        author_marks=author_marks,
        team1=team1,
        team2=team2,
    )


def _build_player_row(
    player: Player,
    results_by_account: dict,
    tankopedia: Tankopedia,
    language: str,
) -> PlayerRow:
    info = player.info
    stats = results_by_account.get(player.account_id)
    tank_id = int(info.tank_id or (stats.tank_id if stats else 0))
    tank_label = _tank_label(tankopedia, tank_id, language)

    avatar_url = ""
    frame_kind = ""
    if info.avatar and info.avatar.info:
        gfx_url = info.avatar.info.gfx_url or ""
        gfx2_url = info.avatar.info.gfx2_url or ""
        avatar_url = _pick_avatar_url(gfx_url, gfx2_url)
        frame_kind = info.avatar.info.kind or ""

    clan_tag = info.clan_tag or ""
    platoon_id = int(info.platoon_id) if info.platoon_id else None
    marks = decode_marks_value(getattr(info, "marks", None))

    if stats is None:
        return PlayerRow(
            account_id=int(player.account_id),
            nickname=info.nickname,
            clan_tag=clan_tag or "",
            avatar_url=avatar_url,
            frame_kind=frame_kind,
            tank_id=tank_id,
            tank_label=tank_label,
            damage=0,
            kills=0,
            blocked=0,
            xp=0,
            credits=0,
            marks=marks,
            hits=0,
            penetrations=0,
            mm_rating=None,
            platoon_id=platoon_id,
        )

    mm_rating = float(stats.mm_rating) if stats.mm_rating else None
    return PlayerRow(
        account_id=int(player.account_id),
        nickname=info.nickname,
        clan_tag=clan_tag or "",
        avatar_url=avatar_url,
        frame_kind=frame_kind,
        tank_id=tank_id,
        tank_label=tank_label,
        damage=int(stats.damage_dealt),
        kills=int(stats.n_enemies_destroyed),
        blocked=int(stats.damage_blocked),
        xp=int(stats.base_xp),
        credits=int(stats.credits_earned),
        marks=marks,
        hits=int(stats.n_hits_dealt),
        penetrations=int(stats.n_penetrations_dealt),
        mm_rating=mm_rating,
        platoon_id=platoon_id,
    )


def _pick_avatar_url(gfx_url: str, gfx2_url: str) -> str:
    for url in (gfx2_url, gfx_url):
        if url and not url.lower().endswith(".webp"):
            return url
    return gfx_url or gfx2_url or ""


_TIER_ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
}


def _tier_label(level: int) -> str:
    return _TIER_ROMAN.get(level, str(level))


def _tank_label(tankopedia: Tankopedia, tank_id: int, language: str) -> str:
    if tank_id <= 0:
        return "—"
    tank = tankopedia.get_tank_by_id(tank_id)
    if tank is None:
        return f"#{tank_id}"
    name = tank.ru_name if language == "ru" else tank.en_name
    return f"{_tier_label(tank.level)} {name}"


def _room_type_label(room_type: RoomType) -> str:
    return room_type.name.replace("_", " ").title()
