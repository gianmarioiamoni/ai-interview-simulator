# tests/services/question_ingestion/test_curated_question_mapper.py

from datetime import datetime, timezone

import pytest

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_ingestion.contracts.normalized_question_record import (
    NormalizedQuestionRecord,
)
from services.question_ingestion.contracts.question_metadata import QuestionMetadata
from services.question_ingestion.mappers.curated_question_mapper import (
    PHASE_4A_QUALITY_SCORE,
    CuratedQuestionMapper,
    CuratedQuestionMappingError,
)


def _build_record(
    text: str = "What is recursion and how does it work?",
) -> NormalizedQuestionRecord:

    return NormalizedQuestionRecord(
        text=text,
        source="pilot_dataset",
        ingestion_metadata=IngestionMetadata(
            source_name="pilot_dataset",
            source_type="huggingface",
            dataset_version="v1",
            ingestion_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )


def test_map_happy_path() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        role=RoleType.BACKEND_ENGINEER,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        level=SeniorityLevel.JUNIOR,
        difficulty=2,
    )

    curated = mapper.map(
        record=record,
        metadata=metadata,
    )

    assert curated.question == record.text
    assert curated.role == RoleType.BACKEND_ENGINEER
    assert curated.area == InterviewArea.TECH_TECHNICAL_KNOWLEDGE
    assert curated.seniority == SeniorityLevel.JUNIOR
    assert curated.difficulty == 2
    assert curated.source == "pilot_dataset"
    assert curated.quality_score == PHASE_4A_QUALITY_SCORE
    assert curated.domains == [InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value]
    assert curated.tags == []
    assert curated.expected_topics == []


def test_map_generates_deterministic_id() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record(
        text="Explain polymorphism in object-oriented programming.",
    )

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    )

    first = mapper.map(record=record, metadata=metadata)
    second = mapper.map(record=record, metadata=metadata)

    assert first.id == second.id
    assert len(first.id) == 16


def test_map_raises_when_area_missing() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        role=RoleType.BACKEND_ENGINEER,
        area=None,
    )

    with pytest.raises(CuratedQuestionMappingError, match="Area metadata is required"):
        mapper.map(
            record=record,
            metadata=metadata,
        )


def test_map_falls_back_to_mid_seniority() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_DATABASE,
        level=None,
    )

    curated = mapper.map(
        record=record,
        metadata=metadata,
    )

    assert curated.seniority == SeniorityLevel.MID


def test_map_falls_back_to_default_difficulty() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_DATABASE,
        difficulty=None,
    )

    curated = mapper.map(
        record=record,
        metadata=metadata,
    )

    assert curated.difficulty == 3


def test_map_falls_back_to_fullstack_role() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_CODING,
        role=None,
    )

    curated = mapper.map(
        record=record,
        metadata=metadata,
    )

    assert curated.role == RoleType.FULLSTACK_ENGINEER


def test_map_preserves_authored_domains() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_DATABASE,
        domains=["sql", "joins", "aggregation"],
    )

    curated = mapper.map(record=record, metadata=metadata)

    assert curated.domains == ["sql", "joins", "aggregation"]


def test_map_falls_back_to_area_value_when_domains_empty() -> None:
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_DATABASE,
        domains=[],
    )

    curated = mapper.map(record=record, metadata=metadata)

    assert curated.domains == [InterviewArea.TECH_DATABASE.value]


def test_map_backward_compatible_no_domains_field() -> None:
    """Existing callers that omit domains must still get [area.value]."""
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        difficulty=4,
    )

    curated = mapper.map(record=record, metadata=metadata)

    assert curated.domains == [InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value]


def test_map_domains_not_contaminated_by_area() -> None:
    """Authored domains must not be mixed with area.value."""
    mapper = CuratedQuestionMapper()

    record = _build_record()

    metadata = QuestionMetadata(
        area=InterviewArea.TECH_DATABASE,
        domains=["cte", "window_function"],
    )

    curated = mapper.map(record=record, metadata=metadata)

    assert InterviewArea.TECH_DATABASE.value not in curated.domains
    assert curated.domains == ["cte", "window_function"]
