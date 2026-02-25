# tests/domain/contracts/test_question_bank_item.py

import pytest
from pydantic import ValidationError
from domain.contracts.role import Role
from domain.contracts.role import RoleType
from domain.contracts.question_bank_item import QuestionBankItem
from domain.contracts.interview_area import InterviewArea
from domain.contracts.interview_area import InterviewType
from domain.contracts.seniority_level import SeniorityLevel


def test_question_bank_item_is_immutable():
    q = QuestionBankItem(
        id="1",
        text="Explain ACID properties.",
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        level=SeniorityLevel.MID,
        difficulty=3,
    )

    with pytest.raises(ValidationError):
        q.text = "Modified"
