# tests/domain/contracts/test_question_bank_item.py

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from domain.contracts.user.role import Role
from domain.contracts.user.role import RoleType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def test_question_bank_item_is_immutable():
    q = QuestionBankItem(
        id="1",
        text="Explain ACID properties.",
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="unit-test",
            source_type="manual",
            dataset_version="v1",
            ingestion_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )

    with pytest.raises(ValidationError):
        q.text = "Modified"
