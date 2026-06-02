# tests/services/question_ingestion/test_minimal_ingestion_orchestrator.py

from datetime import datetime, timezone
from unittest.mock import MagicMock

from domain.contracts.corpus.curated_question import CuratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_ingestion.contracts.normalization_diagnostics import (
    NormalizationDiagnostics,
)
from services.question_ingestion.contracts.normalization_result import NormalizationResult
from services.question_ingestion.contracts.normalized_question_record import (
    NormalizedQuestionRecord,
)
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.mappers.curated_question_mapper import (
    CuratedQuestionMappingError,
)
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)


def _build_raw_record(
    text: str,
    area: str | None = None,
) -> RawQuestionRecord:

    payload: dict = {"text": text}

    if area is not None:
        payload["area"] = area

    return RawQuestionRecord(
        source="pilot_dataset",
        source_type="huggingface",
        dataset_version="v1",
        raw_payload=payload,
        canonical_payload=payload,
    )


def _build_normalized_record(
    text: str,
    area: InterviewArea | None = None,
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
        area_hint=area,
    )


def test_ingest_runs_normalize_classify_map_pipeline() -> None:
    raw_records = [
        _build_raw_record(
            text="What is Docker and how is it used in deployment?",
            area="technical_technical_knowledge",
        ),
    ]

    normalized = _build_normalized_record(
        text="What is Docker and how is it used in deployment?",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    )

    classified = normalized.model_copy(
        update={
            "role_hint": RoleType.BACKEND_ENGINEER,
            "level_hint": SeniorityLevel.MID,
            "difficulty_hint": 3,
        },
    )

    expected_curated = CuratedQuestion(
        id="deterministic-id",
        question=classified.text,
        role=RoleType.BACKEND_ENGINEER,
        seniority=SeniorityLevel.MID,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        domains=["technical_technical_knowledge"],
        difficulty=3,
        source="pilot_dataset",
        quality_score=0.80,
        tags=[],
        expected_topics=[],
    )

    normalizer = MagicMock()
    normalizer.normalize.return_value = NormalizationResult(
        records=[normalized],
        diagnostics=NormalizationDiagnostics(total_records=1, normalized_records=1),
    )

    classifier = MagicMock()
    classifier.classify.return_value = [classified]

    mapper = MagicMock()
    mapper.map.return_value = expected_curated

    orchestrator = MinimalIngestionOrchestrator(
        normalizer=normalizer,
        classifier=classifier,
        mapper=mapper,
    )

    result = orchestrator.ingest(raw_records)

    normalizer.normalize.assert_called_once_with(raw_records)
    classifier.classify.assert_called_once_with([normalized])
    mapper.map.assert_called_once()
    assert result == [expected_curated]


def test_ingest_skips_records_without_area_metadata() -> None:
    raw_records = [
        _build_raw_record(
            text="Describe a time you resolved a team conflict.",
        ),
    ]

    normalized = _build_normalized_record(
        text="Describe a time you resolved a team conflict.",
        area=None,
    )

    normalizer = MagicMock()
    normalizer.normalize.return_value = NormalizationResult(
        records=[normalized],
        diagnostics=NormalizationDiagnostics(total_records=1, normalized_records=1),
    )

    classifier = MagicMock()
    classifier.classify.return_value = [normalized]

    mapper = MagicMock()
    mapper.map.side_effect = CuratedQuestionMappingError("Area metadata is required.")

    orchestrator = MinimalIngestionOrchestrator(
        normalizer=normalizer,
        classifier=classifier,
        mapper=mapper,
    )

    result = orchestrator.ingest(raw_records)

    assert result == []


def test_ingest_integration_with_real_components() -> None:
    orchestrator = MinimalIngestionOrchestrator()

    raw_records = [
        _build_raw_record(
            text="Explain normalization in relational databases.",
            area="technical_database",
        ),
        _build_raw_record(
            text="How would you design a scalable notification system?",
            area="technical_case_study",
        ),
    ]

    result = orchestrator.ingest(raw_records)

    assert len(result) == 2

    areas = {question.area for question in result}

    assert InterviewArea.TECH_DATABASE in areas
    assert InterviewArea.TECH_CASE_STUDY in areas

    for question in result:
        assert question.source == "pilot_dataset"
        assert question.quality_score == 0.80
        assert len(question.id) == 16
