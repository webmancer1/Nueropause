from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import DB_PATH


@dataclass
class SessionLog:
    active_minutes: int
    break_count: int
    timestamp: str


class Database:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    active_minutes INTEGER NOT NULL,
                    break_count INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def log_session(self, active_minutes: int, break_count: int) -> None:
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO session_logs (active_minutes, break_count, timestamp)
                VALUES (?, ?, ?)
                """,
                (active_minutes, break_count, timestamp),
            )
            conn.commit()
