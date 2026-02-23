# infrastructure/persistence/sqlite/models.py

# This module contains the SQLAlchemy models for the SQLite database.

from sqlite3 import Connection


def create_questions_table(conn: Connection) -> None:
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS question_bank (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            interview_type TEXT NOT NULL,
            area TEXT NOT NULL,
            role TEXT NOT NULL,
            level TEXT NOT NULL,
            difficulty TEXT NOT NULL
        )
        """
    )

    conn.commit()
