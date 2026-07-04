from pydantic import BaseModel, field_validator

class AccountSearchItem(BaseModel):
    account_id: int
    nickname: str


class RatingStatistics(BaseModel):
    spotted: int
    calibration_battles_left: int
    hits: int
    frags: int
    recalibration_start_time: int
    mm_rating: int
    wins: int
    losses: int
    is_recalibration: bool
    capture_points: int
    battles: int
    current_season: int
    damage_dealt: int
    damage_received: int
    shots: int
    frags8p: int
    xp: int
    win_and_survived: int
    survived_battles: int
    dropped_capture_points: int
    max_xp: int = 0
    max_xp_tank_id: int = 0

    @field_validator("max_xp", "max_xp_tank_id", mode="before")
    @classmethod
    def none_to_zero(cls, v):
        return 0 if v is None else v


class AllStatistics(BaseModel):
    spotted: int
    max_frags_tank_id: int
    hits: int
    max_frags: int
    frags: int
    wins: int
    losses: int
    capture_points: int
    battles: int
    damage_dealt: int
    damage_received: int
    shots: int
    frags8p: int
    xp: int
    win_and_survived: int
    survived_battles: int
    dropped_capture_points: int
    max_xp: int
    max_xp_tank_id: int

class Statistics(BaseModel):
    all: AllStatistics
    rating: RatingStatistics

class Private(BaseModel):
    gold: int = 0
    free_xp: int = 0
    credits: int = 0
    is_premium: bool = False
    premium_expires_at: int = 0

class AccountStatsItem(BaseModel):
    statistics: Statistics
    account_id: int
    nickname: str
    created_at: int
    updated_at: int
    private: Private = Private()
    last_battle_time: int


class AllTankStats(BaseModel):
    spotted: int
    hits: int
    frags: int
    max_xp: int
    wins: int
    losses: int
    capture_points: int
    battles: int
    damage_dealt: int
    damage_received: int
    max_frags: int
    shots: int
    frags8p: int
    xp: int
    win_and_survived: int
    survived_battles: int
    dropped_capture_points: int

class TankStats(BaseModel):
    all: AllTankStats
    last_battle_time: int
    account_id: int
    mark_of_mastery: int
    battle_life_time: int
    tank_id: int
