# tests/services/question_intelligence/test_sql_pipeline_corpus_quota.py
"""
Unit tests for corpus_quota enforcement in SQLQuestionPipeline.

Validates that:
  - corpus_quota caps retrieved corpus questions at the configured limit
  - LLM generation fills remaining slots when corpus_quota < questions_per_area
  - corpus_quota=None preserves legacy behaviour (corpus fills as much as available)
  - corpus_quota > questions_per_area is clamped to questions_per_area
"""

from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _bank_item(doc_id: str = "sql-001") -> QuestionBankItem:
    from datetime import datetime, timezone
    from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata

    return QuestionBankItem(
        id=doc_id,
        text="Write a SQL query to find duplicate records in a table.",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp=datetime(1970, 1, 1, tzinfo=timezone.utc),
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
        ),
    )


def _sql_question(doc_id: str = "q-001", origin: QuestionOriginType = QuestionOriginType.RETRIEVAL) -> Question:
    return Question(
        id=doc_id,
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.DATABASE,
        prompt="Write a SQL query to find duplicate records.",
        difficulty=QuestionDifficulty.MEDIUM,
        provenance=QuestionProvenance(
            origin_type=origin,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
        ),
    )


def _llm_question(doc_id: str = "llm-001") -> Question:
    return _sql_question(doc_id, origin=QuestionOriginType.LLM_GENERATED)


def _build_pipeline(
    retrieved_items: list[QuestionBankItem],
    enriched_question_factory=None,
    generated_questions: list[Question] | None = None,
) -> SQLQuestionPipeline:
    """Build a pipeline with mocked retrieval, enrichment and generation."""
    retrieval_service = MagicMock()
    sql_generator = MagicMock()

    # retrieve_sql_candidates → returns retrieved_items
    with patch(
        "services.question_intelligence.pipelines.sql_question_pipeline.retrieve_sql_candidates",
        return_value=retrieved_items,
    ):
        pass  # patch applied inside test

    if enriched_question_factory is None:
        enriched_question_factory = lambda item: _sql_question(f"enriched-{item.id}")

    sql_generator.enrich_from_prompt.side_effect = enriched_question_factory
    sql_generator.generate.return_value = generated_questions or [_llm_question()]

    return SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=sql_generator,
    )


# ─── tests ────────────────────────────────────────────────────────────────────

@patch("services.question_intelligence.pipelines.sql_question_pipeline.retrieve_sql_candidates")
def test_corpus_quota_caps_retrieved_questions(mock_retrieve) -> None:
    """corpus_quota=2 must stop retrieval after 2 corpus questions."""
    items = [_bank_item(f"sql-{i}") for i in range(5)]
    mock_retrieve.return_value = items

    sql_gen = MagicMock()
    sql_gen.enrich_from_prompt.side_effect = lambda seed_prompt, **kw: _sql_question(
        f"enriched-{seed_prompt[:8]}"
    )
    # generate must return enough questions to fill remaining 2 slots
    sql_gen.generate.return_value = [_llm_question(f"llm-{i}") for i in range(2)]

    pipeline = SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=sql_gen,
    )

    questions, _ = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=4,
        corpus_quota=2,
        memory=InterviewRetrievalMemory(),
    )

    assert len(questions) == 4
    # enrichment called for at most 2 items (corpus_quota)
    assert sql_gen.enrich_from_prompt.call_count <= 2
    # LLM generation called once to fill the remaining 2 slots
    sql_gen.generate.assert_called_once()
    llm_call_n = sql_gen.generate.call_args[1].get("n") or sql_gen.generate.call_args[0][0]
    assert llm_call_n == 2


@patch("services.question_intelligence.pipelines.sql_question_pipeline.retrieve_sql_candidates")
def test_corpus_quota_none_fills_corpus_first(mock_retrieve) -> None:
    """corpus_quota=None must use legacy behaviour: fill from corpus first."""
    items = [_bank_item(f"sql-{i}") for i in range(3)]
    mock_retrieve.return_value = items

    sql_gen = MagicMock()
    sql_gen.enrich_from_prompt.side_effect = lambda seed_prompt, **kw: _sql_question(
        f"enriched-{seed_prompt[:8]}"
    )
    sql_gen.generate.return_value = []

    pipeline = SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=sql_gen,
    )

    questions, _ = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=3,
        corpus_quota=None,
        memory=InterviewRetrievalMemory(),
    )

    assert len(questions) == 3
    assert sql_gen.enrich_from_prompt.call_count == 3


@patch("services.question_intelligence.pipelines.sql_question_pipeline.retrieve_sql_candidates")
def test_corpus_quota_zero_forces_full_llm_generation(mock_retrieve) -> None:
    """corpus_quota=0 means no corpus questions; all slots filled by LLM."""
    items = [_bank_item(f"sql-{i}") for i in range(5)]
    mock_retrieve.return_value = items

    llm_qs = [_llm_question(f"llm-{i}") for i in range(3)]
    sql_gen = MagicMock()
    sql_gen.enrich_from_prompt.return_value = _sql_question()
    sql_gen.generate.return_value = llm_qs

    pipeline = SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=sql_gen,
    )

    questions, _ = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=3,
        corpus_quota=0,
        memory=InterviewRetrievalMemory(),
    )

    assert len(questions) == 3
    sql_gen.enrich_from_prompt.assert_not_called()


@patch("services.question_intelligence.pipelines.sql_question_pipeline.retrieve_sql_candidates")
def test_corpus_quota_larger_than_questions_per_area_is_clamped(mock_retrieve) -> None:
    """corpus_quota > questions_per_area must be clamped to questions_per_area."""
    items = [_bank_item(f"sql-{i}") for i in range(5)]
    mock_retrieve.return_value = items

    sql_gen = MagicMock()
    sql_gen.enrich_from_prompt.side_effect = lambda seed_prompt, **kw: _sql_question()
    sql_gen.generate.return_value = []

    pipeline = SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=sql_gen,
    )

    questions, _ = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=2,
        corpus_quota=10,
        memory=InterviewRetrievalMemory(),
    )

    assert len(questions) <= 2
    assert sql_gen.enrich_from_prompt.call_count <= 2
