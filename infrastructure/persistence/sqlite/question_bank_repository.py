# app/infrastructure/persistence/sqlite/question_bank_repository.py

from sqlite3 import Connection
from typing import List

from domain.contracts.question_bank_item import QuestionBankItem


class QuestionBankRepository:
    def __init__(self, conn: Connection):
        self._conn = conn

    def save(self, item: QuestionBankItem) -> None:
        cursor = self._conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO question_bank (
                id,
                text,
                interview_type,
                role,
                area,
                level,
                difficulty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.text,
                item.interview_type,
                item.role,
                item.area,
                item.level,
                item.difficulty,
            ),
        )

        self._conn.commit()

    def list_all(self) -> List[QuestionBankItem]:
        cursor = self._conn.cursor()

        rows = cursor.execute("SELECT * FROM question_bank").fetchall()

        return [
            QuestionBankItem(
                id=row[0],
                text=row[1],
                interview_type=row[2],
                role=row[3],
                area=row[4],
                level=row[5],
                difficulty=row[6],
            )
            for row in rows
        ]
