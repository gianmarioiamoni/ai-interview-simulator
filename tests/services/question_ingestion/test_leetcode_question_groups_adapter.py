# tests/services/question_ingestion/test_leetcode_question_groups_adapter.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.adapters.leetcode_question_groups_adapter import (
    CODING_AREA,
    CODING_ROLE,
    LeetcodeQuestionGroupsAdapter,
)


def _adapt_entry(
    entry: dict,
) -> dict:

    adapter = LeetcodeQuestionGroupsAdapter()

    record = adapter.adapt(
        payload=entry,
        source="tech-interview-handbook/question-groups",
        source_type="github",
        dataset_version="v1",
    )

    return record.canonical_payload


def test_generates_interview_style_question_text() -> None:
    payload = _adapt_entry(
        {
            "slug": "two-sum",
            "title": "Two Sum",
            "difficulty": "Easy",
        }
    )

    assert payload["text"] == "How would you solve Two Sum?"


def test_maps_easy_to_junior_and_difficulty_two() -> None:
    payload = _adapt_entry(
        {
            "slug": "two-sum",
            "title": "Two Sum",
            "difficulty": "Easy",
        }
    )

    assert payload["level"] == "junior"
    assert payload["difficulty"] == 2
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.JUNIOR


def test_maps_medium_to_mid_and_difficulty_three() -> None:
    payload = _adapt_entry(
        {
            "slug": "add-two-numbers",
            "title": "Add Two Numbers",
            "difficulty": "Medium",
        }
    )

    assert payload["level"] == "mid"
    assert payload["difficulty"] == 3
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.MID


def test_maps_hard_to_senior_and_difficulty_four() -> None:
    payload = _adapt_entry(
        {
            "slug": "merge-k-sorted-lists",
            "title": "Merge k Sorted Lists",
            "difficulty": "Hard",
        }
    )

    assert payload["level"] == "senior"
    assert payload["difficulty"] == 4
    assert SeniorityLevel(payload["level"]) == SeniorityLevel.SENIOR


def test_assigns_technical_coding_area_and_fullstack_role() -> None:
    payload = _adapt_entry(
        {
            "slug": "valid-parentheses",
            "title": "Valid Parentheses",
            "difficulty": "Easy",
        }
    )

    assert payload["area"] == CODING_AREA
    assert payload["role"] == CODING_ROLE
    assert InterviewArea(payload["area"]) == InterviewArea.TECH_CODING
    assert RoleType(payload["role"]) == RoleType.FULLSTACK_ENGINEER


def test_deduplicates_entries_by_slug() -> None:
    adapter = LeetcodeQuestionGroupsAdapter()

    records = adapter.adapt_document(
        payload={
            "Week 1": [
                {
                    "slug": "two-sum",
                    "title": "Two Sum",
                    "difficulty": "Easy",
                }
            ],
            "Week 2": [
                {
                    "slug": "two-sum",
                    "title": "Two Sum",
                    "difficulty": "Easy",
                }
            ],
        },
        source="tech-interview-handbook/question-groups",
        source_type="github",
        dataset_version="v1",
    )

    assert len(records) == 1
