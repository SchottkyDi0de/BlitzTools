from dataclasses import dataclass
from typing import Any


def _normalize_pickled(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            (key.decode("utf-8") if isinstance(key, bytes) else key): _normalize_pickled(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_pickled(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_pickled(item) for item in value)
    return value


@dataclass
class TurboBattlesStatistics:
    battle_chance: float
    leave_chance: float
    possible_battles_not_for_skip: int
    possible_battles_for_skip: int
    battles_for_skip: int
    battles_not_for_skip: int
    ab_skip: int
    beta: float
    premium_vehicle_difference: int
    ht_difference: int
    alpha: float


@dataclass
class BasePlayerCreate:
    battle_level: int
    battle_category_id: int
    is_mouse_enabled: bool
    matchmaker_type: int
    camouflage_slot: int
    players_battle_categories_ids: dict[int, tuple[int, int]] | None = None
    average_mm_ratings: list[float | None] | None = None
    player_wait_times: dict[int, float] | None = None
    account_database_ids: list[int] | None = None
    turbo_battles_statistics: TurboBattlesStatistics | None = None

    @classmethod
    def from_pickled(cls, value: Any) -> "BasePlayerCreate":
        value = _normalize_pickled(value)
        turbo = None
        if raw_turbo := value.get("turboBattlesStats"):
            turbo = TurboBattlesStatistics(
                battle_chance=raw_turbo["turboBattleChance"],
                leave_chance=raw_turbo["turboLeaveChance"],
                possible_battles_not_for_skip=raw_turbo["possibleTurboBattlesNotForSkip"],
                possible_battles_for_skip=raw_turbo["possibleTurboBattlesForSkip"],
                battles_for_skip=raw_turbo["turboBattlesForSkip"],
                battles_not_for_skip=raw_turbo["turboBattlesNotForSkip"],
                ab_skip=raw_turbo["abSkip"],
                beta=raw_turbo["beta"],
                premium_vehicle_difference=raw_turbo["premiumVehDiff"],
                ht_difference=raw_turbo["htDiff"],
                alpha=raw_turbo["alpha"],
            )

        return cls(
            players_battle_categories_ids=value.get("playersBattleCategoriesIds"),
            battle_level=value["battleLevel"],
            battle_category_id=value["battleCategoryId"],
            is_mouse_enabled=value["mouseEnabled"],
            matchmaker_type=value["mmType"],
            camouflage_slot=value["camouflageSlot"],
            average_mm_ratings=value.get("avgMmr"),
            player_wait_times=value.get("playerWaitTimes"),
            account_database_ids=value.get("accountDatabaseIds"),
            turbo_battles_statistics=turbo,
        )
