# Tests for QuestionSelectionService

from unittest.mock import MagicMock

from domain.contracts.generated_question import GeneratedQuestion
from domain.contracts.question_bank_item import QuestionBankItem
from services.question_intelligence.question_selection_service import (
    QuestionSelectionService,
)
from domain.contracts.role import Role
from domain.contracts.role import RoleType
from domain.contracts.interview_area import InterviewArea


def test_build_area_questions_combines_retrieved_and_generated():

    mock_retrieval = MagicMock()
    mock_generator = MagicMock()

    mock_retrieval.retrieve.return_value = [
        QuestionBankItem(
            id="b1",
            text="Explain ACID properties.",
            interview_type="technical",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            area=InterviewArea.TECH_DATABASE,
            level="mid",
            difficulty=3,
        ),
        QuestionBankItem(
            id="b2",
            text="What is normalization?",
            interview_type="technical",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            area=InterviewArea.TECH_DATABASE,
            level="mid",
            difficulty=2,
        ),
    ]

    mock_generator.generate.return_value = [
        GeneratedQuestion(
            text="Describe two-phase commit.",
            difficulty=4,
        ),
        GeneratedQuestion(
            text="Explain eventual consistency.",
            difficulty=3,
        ),
    ]

    service = QuestionSelectionService(
        retrieval_service=mock_retrieval,
        generator=mock_generator,
    )

    result = service.build_area_questions(
        role=Role(type=RoleType.BACKEND_ENGINEER),
        level="mid",
        interview_type="technical",
        area=InterviewArea.TECH_DATABASE,
    )

    assert len(result) == 4
    assert result[0].area == InterviewArea.TECH_DATABASE
    assert result[2].prompt == "Describe two-phase commit."
