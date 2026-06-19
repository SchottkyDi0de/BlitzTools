from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from lib.config.handler import ConfigHandler
from lib.replay_parser import LiveReplay, parse_live_replay

from lib.olenemer.window.assets import RATING_COEF, load_image
from lib.olenemer.window.models import PlayerRowData, TeamViewData


def _api_base() -> str:
    return ConfigHandler().config.api.base_url.rstrip("/")


def _api_timeout() -> int:
    return ConfigHandler().config.api.timeout


def _fetch_json(path: str, params: dict) -> list | dict:
    import requests

    response = requests.get(f"{_api_base()}{path}", params=params, timeout=_api_timeout())
    response.raise_for_status()
    return response.json()


def _fetch_tank_info(region: str, tank_ids: set[int]) -> dict[int, tuple[str, int, str]]:
    info: dict[int, tuple[str, int, str]] = {}
    if not tank_ids:
        return info

    try:
        tanks = _fetch_json(f"/v1/tankopedia/{region}/tanks", {})
        lookup = {
            int(tank["id"]): (
                tank.get("ru_name") or tank.get("en_name") or "?",
                int(tank.get("level") or 0),
                str(tank.get("category") or ""),
            )
            for tank in tanks
        }
        for tank_id in tank_ids:
            info[tank_id] = lookup.get(tank_id, ("?", 0, ""))
        return info
    except Exception:
        pass

    for tank_id in tank_ids:
        if tank_id <= 0:
            continue
        try:
            data = _fetch_json(f"/v1/tankopedia/{region}/tanks/{tank_id}", {})
            info[tank_id] = (
                data.get("ru_name") or data.get("en_name") or "?",
                int(data.get("level") or 0),
                str(data.get("category") or ""),
            )
        except Exception:
            info[tank_id] = ("?", 0, "")
    return info


def _rating_value(mm_rating: float | None, calibration_battles_left: int | None) -> tuple[int, bool]:
    calibrated = calibration_battles_left == 0 and mm_rating is not None
    if not calibrated:
        return 0, False
    return int(round(3000 + float(mm_rating) * RATING_COEF)), True


def _account_overall_stats(account_stats: dict) -> dict:
    return (account_stats.get("statistics") or {}).get("all") or {}


def _tank_name_char_order(char: str) -> tuple[int, str]:
    if char.isdigit():
        return 0, char
    if char.isascii() and char.isalpha():
        return 1, char.casefold()
    code = ord(char)
    if 0x0400 <= code <= 0x04FF or 0x0500 <= code <= 0x052F:
        return 2, char.casefold()
    return 3, char.casefold()


def tank_name_sort_key(name: str) -> tuple:
    return tuple(_tank_name_char_order(char) for char in name)


def _average_team_rating(rows: list[PlayerRowData]) -> float:
    ratings = [row.rating for row in rows if row.rating > 0]
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def _fetch_account_stats(region: str, account_ids: list[int]) -> dict[int, dict]:
    stats_by_id: dict[int, dict] = {}
    if not account_ids:
        return stats_by_id

    stats_items = _fetch_json(f"/v1/accounts/{region}/stats", {"ids": ",".join(map(str, account_ids))})
    for item in stats_items:
        stats = item.get("stats")
        if not stats or not stats.get("data"):
            continue
        stats_by_id[int(item["account_id"])] = stats["data"]
    return stats_by_id


def build_team_view(
    replay: LiveReplay,
    region: str = "ru",
    team: int = 1,
    *,
    stats_by_id: dict[int, dict] | None = None,
    tank_info: dict[int, tuple[str, int, str]] | None = None,
) -> TeamViewData:
    team_players = replay.team_1 if team == 1 else replay.team_2
    title = "Союзники" if team == 1 else "Противники"
    account_ids = [int(player.account_id) for player in team_players if player.account_id]

    if stats_by_id is None:
        stats_by_id = _fetch_account_stats(region, account_ids)
    if tank_info is None:
        tank_info = _fetch_tank_info(region, {player.tank_id for player in team_players})

    author_clan_tag = next(
        (player.clan_tag for player in team_players if player.nickname == replay.author_nickname),
        None,
    )

    rows: list[PlayerRowData] = []
    for player in sorted(
        team_players,
        key=lambda item: (
            tank_name_sort_key(tank_info.get(item.tank_id, ("", 0, ""))[0]),
            item.nickname.casefold(),
        ),
    ):
        tank_name, tank_level, tank_category = tank_info.get(player.tank_id, ("?", 0, ""))
        account_stats = stats_by_id.get(int(player.account_id or 0), {})
        rating_block = (account_stats.get("statistics") or {}).get("rating") or {}
        mm_rating = rating_block.get("mm_rating")
        calibration_left = rating_block.get("calibration_battles_left")
        rating, calibrated = _rating_value(mm_rating, calibration_left)

        overall = _account_overall_stats(account_stats)
        battles = int(overall.get("battles") or 0)
        wins = int(overall.get("wins") or 0)
        damage = int(overall.get("damage_dealt") or 0)
        winrate = (wins / battles * 100.0) if battles else 0.0
        avg_damage = int(damage / battles) + 1 if battles else 0

        rows.append(
            PlayerRowData(
                nickname=player.nickname,
                clan_tag=player.clan_tag,
                platoon_index=player.platoon_index,
                avatar_url=player.avatar_url,
                frame_kind=player.frame_kind,
                profile_skin_url=player.profile_skin_url,
                tank_level=tank_level,
                tank_category=tank_category,
                tank_name=tank_name,
                marks=player.marks,
                battles=battles,
                winrate=winrate,
                avg_damage=avg_damage,
                rating=rating,
                calibrated=calibrated,
                is_author=player.nickname == replay.author_nickname,
                author_clan_tag=author_clan_tag,
            )
        )

    summary_battles = sum(row.battles for row in rows) / len(rows) if rows else 0.0
    summary_winrate = sum(row.winrate for row in rows) / len(rows) if rows else 0.0
    summary_damage = sum(row.avg_damage for row in rows) / len(rows) if rows else 0.0
    summary_rating = _average_team_rating(rows)

    return TeamViewData(
        title=title,
        rows=rows,
        summary_battles=summary_battles,
        summary_winrate=summary_winrate,
        summary_damage=summary_damage,
        summary_rating=summary_rating,
    )


def replay_region(replay: LiveReplay) -> str:
    return str(replay.region)


def build_teams_view(replay: LiveReplay, region: str | None = None) -> dict[int, TeamViewData]:
    api_region = region or replay_region(replay)
    all_players = replay.all_players
    account_ids = [int(player.account_id) for player in all_players if player.account_id]
    stats_by_id = _fetch_account_stats(api_region, account_ids)
    tank_info = _fetch_tank_info(api_region, {player.tank_id for player in all_players})
    return {
        1: build_team_view(
            replay,
            api_region,
            team=1,
            stats_by_id=stats_by_id,
            tank_info=tank_info,
        ),
        2: build_team_view(
            replay,
            api_region,
            team=2,
            stats_by_id=stats_by_id,
            tank_info=tank_info,
        ),
    }


def prefetch_team_assets(*teams: TeamViewData, workers: int = 8, profile_skins: bool = True) -> None:
    jobs: set[tuple[str, str]] = set()
    for team in teams:
        for row in team.rows:
            if row.avatar_url:
                jobs.add(("avatar", row.avatar_url))
            if profile_skins and row.profile_skin_url:
                jobs.add(("skin", row.profile_skin_url))
    if not jobs:
        return

    with ThreadPoolExecutor(max_workers=workers) as executor:
        list(executor.map(lambda job: load_image(job[1], job[0]), jobs))


def load_teams_for_replay(replay_path: Path | str, *, profile_skins: bool = True) -> tuple[dict[int, TeamViewData], str, LiveReplay]:
    replay = parse_live_replay(replay_path)
    region = replay_region(replay)
    tv_data = build_teams_view(replay, region)
    prefetch_team_assets(tv_data[1], tv_data[2], profile_skins=profile_skins)
    return tv_data, region, replay


def load_team_view(replay_path: Path | str, region: str | None = None, *, team: int = 1) -> TeamViewData:
    replay = parse_live_replay(replay_path)
    api_region = region or replay_region(replay)
    return build_team_view(replay, api_region, team=team)


def load_team_view_async(
    callback: Callable[[TeamViewData | Exception], None],
    replay_path: Path | str,
    region: str | None = None,
    *,
    team: int = 1,
) -> None:
    def worker() -> None:
        try:
            result = load_team_view(replay_path, region=region, team=team)
            callback(result)
        except Exception as exc:
            callback(exc)

    threading.Thread(target=worker, daemon=True).start()
