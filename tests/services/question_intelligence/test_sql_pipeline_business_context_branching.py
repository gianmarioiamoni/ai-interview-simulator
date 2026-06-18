# tests/services/question_intelligence/test_sql_pipeline_business_context_branching.py
"""
Tests for BusinessContext-driven SQL pipeline branching:
- GENERIC uses enrichment (enrich_from_prompt)
- FINTECH uses metadata-only generation (generate, not enrich_from_prompt)
- fallback: None business_context uses enrichment
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.question.sql_domain import SqlDomain
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
    _BUSINESS_CONTEXT_METADATA_ONLY,
)

RETRIEVE_SQL_CANDIDATES = (
    "services.question_intelligence.pipelines.sql_question_pipeline."
    "retrieve_sql_candidates"
)

_VALID_SQL_QUESTION = Question(
    id="q-1",
    area=InterviewArea.TECH_DATABASE,
    type=QuestionType.DATABASE,
    prompt="List all accounts with balance above 10000.",
    difficulty=QuestionDifficulty.MEDIUM,
    provenance=QuestionProvenance(
        origin_type=QuestionOriginType.LLM_GENERATED,
        source_name="test",
        source_type="test",
        dataset_version="v1",
    ),
)


def _bank_item(text: str = "Write a query to count transactions per account.") -> QuestionBankItem:
    return QuestionBankItem(
        id="sql-001",
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=3,
        domains=[SqlDomain.JOIN, SqlDomain.GROUP_BY],
        expected_topics=["COUNT", "GROUP BY"],
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp=datetime(1970, 1, 1, tzinfo=timezone.utc),
        ),
    )


def _build_pipeline(sql_gen: MagicMock) -> SQLQuestionPipeline:
    return SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=sql_gen,
    )


class TestBusinessContextMetadataOnlySet:
    def test_fintech_in_metadata_only_set(self):
        assert BusinessContext.FINTECH in _BUSINESS_CONTEXT_METADATA_ONLY

    def test_generic_not_in_metadata_only_set(self):
        assert BusinessContext.GENERIC not in _BUSINESS_CONTEXT_METADATA_ONLY

    def test_ecommerce_not_in_metadata_only_set(self):
        assert BusinessContext.ECOMMERCE not in _BUSINESS_CONTEXT_METADATA_ONLY

    def test_saas_not_in_metadata_only_set(self):
        assert BusinessContext.SAAS not in _BUSINESS_CONTEXT_METADATA_ONLY


class TestGenericContextUsesEnrichment:
    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_generic_calls_enrich_from_prompt(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.enrich_from_prompt.return_value = _VALID_SQL_QUESTION
        sql_gen.generate.return_value = []

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.GENERIC,
        )

        sql_gen.enrich_from_prompt.assert_called_once()
        # generate should NOT be called for the corpus item
        assert sql_gen.generate.call_count == 0

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_none_context_calls_enrich_from_prompt(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.enrich_from_prompt.return_value = _VALID_SQL_QUESTION
        sql_gen.generate.return_value = []

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=None,
        )

        sql_gen.enrich_from_prompt.assert_called_once()


class TestFintechContextUsesMetadataGeneration:
    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_calls_generate_not_enrich(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        sql_gen.enrich_from_prompt.assert_not_called()
        sql_gen.generate.assert_called()

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_generate_receives_domains_from_item(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        call_kwargs = sql_gen.generate.call_args[1]
        assert "domains" in call_kwargs
        assert call_kwargs["domains"] is not None
        assert "join" in call_kwargs["domains"]

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_generate_receives_difficulty_label(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        call_kwargs = sql_gen.generate.call_args[1]
        assert "difficulty_label" in call_kwargs
        assert call_kwargs["difficulty_label"] is not None

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_generate_receives_scenario_anchor(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        call_kwargs = sql_gen.generate.call_args[1]
        assert "scenario_anchor" in call_kwargs
        assert call_kwargs["scenario_anchor"] is not None

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_generate_called_with_n_1_per_item(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        # First generate call (from _generate_from_item_metadata) should have n=1
        first_call_kwargs = sql_gen.generate.call_args_list[0][1]
        assert first_call_kwargs.get("n") == 1

    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_fintech_non_actionable_item_still_goes_to_generate(self, mock_retrieve):
        """FINTECH path skips actionable check — item.text is ignored."""
        mock_retrieve.return_value = [_bank_item(text="Explain ACID properties.")]
        sql_gen = MagicMock()
        sql_gen.generate.return_value = [_VALID_SQL_QUESTION]

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
            business_context=BusinessContext.FINTECH,
        )

        # Should have been called via metadata path, not skipped
        sql_gen.enrich_from_prompt.assert_not_called()
        sql_gen.generate.assert_called()


class TestBackwardCompatibility:
    @patch(RETRIEVE_SQL_CANDIDATES)
    def test_no_business_context_uses_enrichment(self, mock_retrieve):
        mock_retrieve.return_value = [_bank_item()]
        sql_gen = MagicMock()
        sql_gen.enrich_from_prompt.return_value = _VALID_SQL_QUESTION
        sql_gen.generate.return_value = []

        pipeline = _build_pipeline(sql_gen)
        pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
            corpus_quota=1,
            memory=InterviewRetrievalMemory(),
        )

        sql_gen.enrich_from_prompt.assert_called_once()
