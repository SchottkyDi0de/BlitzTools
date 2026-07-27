import json

from pathlib import Path
from typing import Any

from utils.resource_path import get_files_path
from utils.singleton_factory import singleton
from lib.db.services.session import SessionService

DB_PATH = get_files_path() / "db"
TABLES = {
    "sessions": "sessions.json"
}

@singleton
class DatabaseClient:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.tables = TABLES
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_tables()
        self._init_datas()
        self._init_services()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()


    def _init_tables(self) -> None:
        for table in TABLES.values():
            table_path = self.db_path / table
            if not table_path.exists():
                with open(table_path, "w", encoding="utf-8-sig") as f:
                    json.dump([], f, ensure_ascii=False, indent=4, sort_keys=True)

    def _load_table(self, table: str) -> list[dict[str, Any]]:
        table_path = self.db_path / self.tables[table]
        with open(table_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    def _init_datas(self) -> None:
        self.data = {}
        for table in self.tables:
            self.data[table] = self._load_table(table)

    def _init_services(self) -> None:
        self.sessions = SessionService(self)


    def save(self, table: str | None = None) -> None:
        if table:
            table_path = self.db_path / self.tables[table]
            with open(table_path, "w", encoding="utf-8-sig") as f:
                json.dump(self.data[table], f, ensure_ascii=False, indent=4, sort_keys=True)
        else:
            for table, data in self.data.items():
                table_path = self.db_path / self.tables[table]
                with open(table_path, "w", encoding="utf-8-sig") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)
