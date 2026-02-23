# tests/services/test_question_bank_loader.py

from unittest.mock import MagicMock

from domain.contracts.question_bank_item import QuestionBankItem
from services.question_bank_loader import QuestionBankLoader


def test_load_converts_dict_to_question_bank_item() -> None:
    mock_repository = MagicMock()
    loader = QuestionBankLoader(mock_repository)

    raw_items = [
        {
            "text": "Explain ACID properties.",
            "interview_type": "technical",
            "role": "backend",
            "area": "databases",
            "level": "mid",
            "difficulty": 3,
        }
    ]

    loader.load(raw_items)

    assert mock_repository.save.called
    args, _ = mock_repository.save.call_args
    saved_item = args[0]

    assert isinstance(saved_item, QuestionBankItem)
    assert saved_item.text == "Explain ACID properties."
    assert saved_item.interview_type == "technical"
    assert saved_item.role == "backend"
    assert saved_item.area == "databases"
    assert saved_item.level == "mid"
    assert saved_item.difficulty == 3


def test_load_generates_uuid_for_each_item() -> None:
    mock_repository = MagicMock()
    loader = QuestionBankLoader(mock_repository)

    raw_items = [
        {
            "text": "Question 1",
            "interview_type": "technical",
            "role": "backend",
            "area": "databases",
            "level": "mid",
            "difficulty": 3,
        },
        {
            "text": "Question 2",
            "interview_type": "hr",
            "role": "frontend",
            "area": "communication",
            "level": "junior",
            "difficulty": 2,
        },
    ]

    loader.load(raw_items)

    assert mock_repository.save.call_count == 2

    first_call = mock_repository.save.call_args_list[0]
    second_call = mock_repository.save.call_args_list[1]

    first_item = first_call[0][0]
    second_item = second_call[0][0]

    assert first_item.id != second_item.id
    assert len(first_item.id) > 0
    assert len(second_item.id) > 0


def test_load_handles_multiple_items() -> None:
    mock_repository = MagicMock()
    loader = QuestionBankLoader(mock_repository)

    raw_items = [
        {
            "text": f"Question {i}",
            "interview_type": "technical",
            "role": "backend",
            "area": "databases",
            "level": "mid",
            "difficulty": 3,
        }
        for i in range(5)
    ]

    loader.load(raw_items)

    assert mock_repository.save.call_count == 5
