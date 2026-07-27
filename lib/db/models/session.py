from pydantic import BaseModel

class SessionData(BaseModel):
    statistics: dict[str, dict[str, int]]
    tank_statistics: list[dict[str, dict[str, int] | int]]
    mm_rating: int
    credits: int
    free_xp: int
    gold: int

class Session(BaseModel):
    session_id: int
    started_at: int
    ended_at: int
    nickname: str
    account_id: int
    on_start_data: SessionData | None = None
    on_end_data: SessionData | None = None
