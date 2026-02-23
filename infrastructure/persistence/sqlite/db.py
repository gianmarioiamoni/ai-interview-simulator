# infrastructure/persistence/sqlite/db.py

import sqlite3
from pathlib import Path


DB_PATH = Path("data/questions.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)
