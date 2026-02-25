# Tests for QuestionSetBuilder

from unittest.mock import MagicMock

from domain.contracts.question import Question, QuestionType
from services.question_intelligence.question_set_builder import (
    QuestionSetBuilder,
)
from domain.contracts.role import Role
from domain.contracts.role import RoleType


def create_fake_questions(area: str):
    return [
        Question(
            id=f"{area}-1",
            area=area,
            type=QuestionType.WRITTEN,
            prompt=f"{area} question 1",
            difficulty=3,
        ),
        Question(
            id=f"{area}-2",
            area=area,
            type=QuestionType.WRITTEN,
            prompt=f"{area} question 2",
            difficulty=3,
        ),
        Question(
            id=f"{area}-3",
            area=area,
            type=QuestionType.WRITTEN,
            prompt=f"{area} question 3",
            difficulty=3,
        ),
        Question(
            id=f"{area}-4",
            area=area,
            type=QuestionType.WRITTEN,
            prompt=f"{area} question 4",
            difficulty=3,
        ),
    ]


def test_build_creates_20_questions():
    mock_selection = MagicMock()

    areas = ["a1", "a2", "a3", "a4", "a5"]

    mock_selection.build_area_questions.side_effect = [
        create_fake_questions(area) for area in areas
    ]

    builder = QuestionSetBuilder(mock_selection)

    result = builder.build(
        role=Role(type=RoleType.BACKEND_ENGINEER),
        level="mid",
        interview_type="technical",
        areas=areas,
    )

    assert len(result) == 20


def test_duplicate_detection_raises():
    import pytest
    
    mock_selection = MagicMock()

    duplicate_questions = create_fake_questions("a1")

    mock_selection.build_area_questions.side_effect = [
        duplicate_questions,
        duplicate_questions,
        duplicate_questions,
        duplicate_questions,
        duplicate_questions,
    ]

    builder = QuestionSetBuilder(mock_selection)

    with pytest.raises(ValueError, match="Duplicate questions detected"):
        builder.build(
            role=Role(type=RoleType.BACKEND_ENGINEER),
            level="mid",
            interview_type="technical",
            areas=["a1", "a2", "a3", "a4", "a5"],
        )


def test_area_with_wrong_question_count_raises():
    import pytest
    
    mock_selection = MagicMock()

    # First area returns only 3 questions instead of 4
    mock_selection.build_area_questions.side_effect = [
        create_fake_questions("a1")[:3],  # Only 3 questions
    ]

    builder = QuestionSetBuilder(mock_selection)

    with pytest.raises(ValueError, match="did not produce exactly 4 questions"):
        builder.build(
            role=Role(type=RoleType.BACKEND_ENGINEER),
            level="mid",
            interview_type="technical",
            areas=["a1"],
        )


def test_total_not_20_questions_raises():
    import pytest
    
    mock_selection = MagicMock()

    # Only 3 areas instead of 5, will produce 12 questions instead of 20
    areas = ["a1", "a2", "a3"]

    mock_selection.build_area_questions.side_effect = [
        create_fake_questions(area) for area in areas
    ]

    builder = QuestionSetBuilder(mock_selection)

    with pytest.raises(ValueError, match="Expected 20 questions"):
        builder.build(
            role=Role(type=RoleType.BACKEND_ENGINEER),
            level="mid",
            interview_type="technical",
            areas=areas,
        )
