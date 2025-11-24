import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str = "database.db"):
        self.path = Path(path)
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    # -------------------- CONNECTION --------------------

    def connect(self):
        """Открывает соединение с БД."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.path)
            self.cursor = self.conn.cursor()
            self.conn.execute("PRAGMA foreign_keys = ON;")
        return self

    def close(self):
        """Закрывает соединение."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None
            self.cursor = None

    # -------------------- MIGRATIONS --------------------

    def migrate(self):
        """
        Выполняет миграции — создание необходимых таблиц.
        Добавляй сюда любые новые таблицы.
        """
        self.connect()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                rating_battles INTEGER NOT NULL,
                default_battles INTEGER NOT NULL,
                rating INTEGER,
                battles INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                shots INTEGER NOT NULL,
                hits INTEGER NOT NULL,
                frags INTEGER NOT NULL,
                damage_dealt INTEGER NOT NULL,
                damage_received INTEGER NOT NULL,
                survived_battles INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                capture_points INTEGER NOT NULL,
                dropped_capture_points INTEGER NOT NULL,
                started_at TIMESTAMP,
                ended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self.conn.commit()

    # -------------------- QUERY HELPERS --------------------

    def execute(self, query: str, params: tuple = ()):
        """Выполняет запрос без возврата результата."""
        self.connect()
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetchone(self, query: str, params: tuple = ()):
        """Возвращает одну строку."""
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        """Возвращает список строк."""
        self.connect()
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
