# app/application/services/question_bank_loader.py

import uuid
from typing import List

from domain.contracts.question_bank_item import QuestionBankItem
from domain.contracts.interview_area import InterviewType, InterviewArea
from domain.contracts.role import Role, RoleType
from domain.contracts.seniority_level import SeniorityLevel
from infrastructure.persistence.sqlite.question_bank_repository import (
    QuestionBankRepository,
)


class QuestionBankLoader:
    def __init__(self, repository: QuestionBankRepository):
        self._repository = repository

    @staticmethod
    def _normalize_role(value: str) -> RoleType:
        mapping = {
            "backend": "backend_engineer",
            "frontend": "frontend_engineer",
            "fullstack": "fullstack_engineer",
            "devops": "devops_engineer",
            "data": "data_engineer",
            "ml": "ml_engineer",
            "qa": "qa_engineer",
        }
        normalized = mapping.get(value, value)
        return RoleType(normalized)

    @staticmethod
    def _normalize_area(value: str) -> InterviewArea:
        mapping = {
            "databases": InterviewArea.TECH_DATABASE,
            "communication": InterviewArea.HR_TECHNICAL_KNOWLEDGE,
        }
        normalized = mapping.get(value, value)
        return InterviewArea(normalized)

    def load(self, items: List[dict]) -> None:
        for raw in items:

            item = QuestionBankItem(
                id=str(uuid.uuid4()),
                text=raw["text"],
                interview_type=InterviewType(raw["interview_type"]),
                role=Role(type=self._normalize_role(raw["role"])),
                area=self._normalize_area(raw["area"]),
                level=SeniorityLevel(raw["level"]),
                difficulty=raw["difficulty"],
            )

            self._repository.save(item)
