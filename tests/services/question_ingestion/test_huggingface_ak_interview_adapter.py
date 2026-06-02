# tests/services/question_ingestion/test_huggingface_ak_interview_adapter.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.adapters.huggingface_ak_interview_adapter import (
    AK_INTERVIEW_ROLE,
    AREA_HR_SITUATIONAL,
    AREA_TECHNICAL_CODING,
    AREA_TECHNICAL_DATABASE,
    AREA_TECHNICAL_KNOWLEDGE,
    HuggingFaceAkInterviewAdapter,
)


def _adapt_question(
    question: str,
    answer: str = "Sample answer.",
    label: int = 8,
) -> dict:

    adapter = HuggingFaceAkInterviewAdapter()

    record = adapter.adapt(
        payload={
            "text": f"Question: {question} Answer: {answer}",
            "label": label,
        },
        source="akshar2109/ak_interview",
        source_type="huggingface",
        dataset_version="v1",
    )

    return record.canonical_payload


def test_extract_question_from_question_answer_format() -> None:
    adapter = HuggingFaceAkInterviewAdapter()

    record = adapter.adapt(
        payload={
            "text": "Question: What is recursion? Answer: Recursion is when a function calls itself.",
            "label": 8,
        },
        source="akshar2109/ak_interview",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == "What is recursion?"


def test_resolve_recursion_as_coding_junior() -> None:
    payload = _adapt_question("What is recursion?")

    assert payload["area"] == AREA_TECHNICAL_CODING
    assert payload["level"] == "junior"
    assert InterviewArea(payload["area"]) == InterviewArea.TECH_CODING
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.JUNIOR


def test_resolve_strengths_as_hr_mid() -> None:
    payload = _adapt_question("What are your strengths?")

    assert payload["area"] == AREA_HR_SITUATIONAL
    assert payload["level"] == "mid"
    assert InterviewArea(payload["area"]) == InterviewArea.HR_SITUATIONAL
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.MID


def test_resolve_normalization_as_database() -> None:
    payload = _adapt_question("Explain normalization.")

    assert payload["area"] == AREA_TECHNICAL_DATABASE
    assert InterviewArea(payload["area"]) == InterviewArea.TECH_DATABASE


def test_assigns_fullstack_engineer_role() -> None:
    adapter = HuggingFaceAkInterviewAdapter()

    record = adapter.adapt(
        payload={
            "text": "Question: What is Docker? Answer: Docker packages applications into containers.",
            "label": 8,
        },
        source="akshar2109/ak_interview",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["role"] == AK_INTERVIEW_ROLE
    assert RoleType(record.canonical_payload["role"]) == RoleType.FULLSTACK_ENGINEER


def test_default_area_is_technical_knowledge() -> None:
    payload = _adapt_question("What is REST API?")

    assert payload["area"] == AREA_TECHNICAL_KNOWLEDGE


def test_preserves_raw_payload_and_does_not_map_label_to_difficulty() -> None:
    adapter = HuggingFaceAkInterviewAdapter()

    raw_payload = {
        "text": "Question: What is recursion? Answer: Recursion is when a function calls itself.",
        "label": 9,
    }

    record = adapter.adapt(
        payload=raw_payload,
        source="akshar2109/ak_interview",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.raw_payload == raw_payload
    assert "difficulty" not in record.canonical_payload
    assert "difficulty_hint" not in record.canonical_payload
