import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.db.client import DatabaseClient

from lib.db.models.session import Session, SessionData
from lib.db.exceptions import session as Exc
from lib.api.models import AccountStatsItem, TankStats


class SessionService:
    def __init__(self, db: "DatabaseClient") -> None:
        self.db = db
        self.table_name = "sessions"
        self.data: list = self.db.data.get(self.table_name, [])


    def add(self, session: Session) -> Session:
        self.data.append(session.model_dump())
        self.db.save(self.table_name)
        return session

    def update(self, session: Session) -> Session:
        for sess in self.data:
            if sess.get("session_id") == session.session_id:
                sess.update(session.model_dump())
                self.db.save(self.table_name)
                return Session.model_validate(session)
        raise Exc.SessionNotFoundError(f"Session with ID {session.session_id} not found.")


    def get(self, session_id: int) -> Session:
        for session in self.data:
            if session.get("session_id") == session_id:
                return Session.model_validate(session)
        raise Exc.SessionNotFoundError(f"Session with ID {session_id} not found.")

    def get_all(self) -> list[Session]:
        return [Session.model_validate(session) for session in self.data]

    def get_latest(self) -> Session | None:
        return self.get_all()[-1] if self.data else None


    def is_latest_session_ended(self) -> bool:
        latest_session = self.get_latest()
        if latest_session is None:
            return True
        return latest_session.ended_at != 0

    def end_latest_session(self, user_data: AccountStatsItem, tank_data: list[TankStats]) -> Session:
        latest_session = self.get_latest()
        if latest_session is None:
            raise Exc.NoActiveSessionError("No active session to end.")

        if latest_session.ended_at != 0:
            raise Exc.SessionAlreadyEndedError("The latest session has already ended.")

        latest_session.ended_at = int(time.time())
        latest_session.on_end_data = SessionData(
            statistics      = user_data.statistics.model_dump(),
            tank_statistics = [data.model_dump() for data in tank_data],
            mm_rating       = user_data.statistics.rating.mm_rating,
            credits         = user_data.private.credits,
            free_xp         = user_data.private.free_xp,
            gold            = user_data.private.gold
        )
        self.update(latest_session)
        self.db.save(self.table_name)
        return latest_session


    def create(self, user_data: AccountStatsItem, tank_data: list[TankStats]) -> Session:
        if not self.is_latest_session_ended():
            raise Exc.SessionNotEndedError("The latest session has not ended yet.")

        session_data = SessionData(
            statistics      = user_data.statistics.model_dump(),
            tank_statistics = [data.model_dump() for data in tank_data],
            mm_rating       = user_data.statistics.rating.mm_rating,
            credits         = user_data.private.credits,
            free_xp         = user_data.private.free_xp,
            gold            = user_data.private.gold
        )
        session = Session(
            session_id    = len(self.data) + 1,
            started_at    = int(time.time()),
            ended_at      = 0,
            nickname      = user_data.nickname,
            account_id    = user_data.account_id,
            on_start_data = session_data
        )
        return self.add(session)
