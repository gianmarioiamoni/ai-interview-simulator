# tests/services/question_ingestion/test_behavioral_markdown_adapter.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.adapters.behavioral_markdown_adapter import (
    AREA_HR_BACKGROUND,
    AREA_HR_BRAIN_TEASER,
    AREA_HR_SITUATIONAL,
    BEHAVIORAL_ROLE,
    BehavioralMarkdownAdapter,
)


def _adapt_text(
    text: str,
) -> dict:

    adapter = BehavioralMarkdownAdapter()

    record = adapter.adapt(
        payload={
            "text": text,
        },
        source="tech-interview-handbook/behavioral-interview-questions",
        source_type="github",
        dataset_version="v1",
    )

    return record.canonical_payload


def test_extract_questions_from_markdown_document() -> None:
    adapter = BehavioralMarkdownAdapter()

    content = """
## Sample section

1. Why do you want to work for X company?
- Tell me about a time when you had a conflict with a co-worker.
- If you had an unlimited budget and you could buy one gift for one person, what would you buy and who would you buy it for?
"""

    records = adapter.adapt_document(
        content=content,
        source="tech-interview-handbook/behavioral-interview-questions",
        source_type="github",
        dataset_version="v1",
    )

    texts = [record.canonical_payload["text"] for record in records]

    assert len(records) == 3
    assert "Why do you want to work for X company?" in texts


def test_resolve_conflict_as_hr_situational() -> None:
    payload = _adapt_text(
        "Tell me about a time when you had a conflict with a co-worker.",
    )

    assert payload["area"] == AREA_HR_SITUATIONAL
    assert InterviewArea(payload["area"]) == InterviewArea.HR_SITUATIONAL


def test_resolve_motivation_as_hr_background() -> None:
    payload = _adapt_text(
        "Why do you want to work for X company?",
    )

    assert payload["area"] == AREA_HR_BACKGROUND
    assert InterviewArea(payload["area"]) == InterviewArea.HR_BACKGROUND


def test_resolve_budget_gift_as_hr_brain_teaser() -> None:
    payload = _adapt_text(
        "If you had an unlimited budget and you could buy one gift for one person, "
        "what would you buy and who would you buy it for?",
    )

    assert payload["area"] == AREA_HR_BRAIN_TEASER
    assert InterviewArea(payload["area"]) == InterviewArea.HR_BRAIN_TEASER


def test_assigns_fullstack_engineer_role_and_mid_level() -> None:
    payload = _adapt_text(
        "Tell me about a time you met a tight deadline.",
    )

    assert payload["role"] == BEHAVIORAL_ROLE
    assert payload["level"] == "mid"
    assert RoleType(payload["role"]) == RoleType.FULLSTACK_ENGINEER
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.MID


def test_deduplicates_repeated_questions_in_document() -> None:
    adapter = BehavioralMarkdownAdapter()

    content = """
1. Why do you want to work for X company?
1. Why do you want to work for X company?
"""

    records = adapter.adapt_document(
        content=content,
        source="tech-interview-handbook/behavioral-interview-questions",
        source_type="github",
        dataset_version="v1",
    )

    assert len(records) == 1
