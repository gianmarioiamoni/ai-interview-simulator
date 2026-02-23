# app/application/services/question_bank_loader.py

# QuestionBankLoader
#
# Responsibility:
# Loads curated dataset entries into the Question Bank.
# This operates on QuestionBankItem, not runtime Question.

import uuid
from typing import List

from domain.contracts.question_bank_item import QuestionBankItem
from infrastructure.persistence.sqlite.question_bank_repository import (
    QuestionBankRepository,
)


class QuestionBankLoader:
    def __init__(self, repository: QuestionBankRepository):
        self._repository = repository

    def load(self, items: List[dict]) -> None:
        for raw in items:
            item = QuestionBankItem(
                id=str(uuid.uuid4()),
                text=raw["text"],
                interview_type=raw["interview_type"],
                role=raw["role"],
                area=raw["area"],
                level=raw["level"],
                difficulty=raw["difficulty"],
            )

            self._repository.save(item)
