# tests/services/question_intelligence/test_domain_propagation.py
#
# Regression tests for the domain propagation chain:
# RetrievalCandidate → QuestionBankItem → QuestionProvenance → Question

import uuid
from datetime import datetime, timezone

import pytest
from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
    CORPUS_INDEX_DATASET_VERSION,
)
from services.question_intelligence.pipelines.written_question_mapper import (
    WrittenQuestionMapper,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


_BASE_METADATA = {
    "document_id": "test_doc_001",
    "role": "backend_engineer",
    "area": "technical_database",
    "seniority": "mid",
    "difficulty": 3,
    "source": "manual_sql_expansion_wave1",
}


def _candidate(domains_value: str | None = None) -> RetrievalCandidate:
    meta = dict(_BASE_METADATA)
    if domains_value is not None:
        meta["domains"] = domains_value
    return RetrievalCandidate(
        document=Document(page_content="Write a join query.", metadata=meta),
        semantic_score=0.8,
        quality_score=0.9,
        final_score=0.85,
        adaptive_score=0.88,
    )


def _bank_item(domains: list[str]) -> QuestionBankItem:
    return QuestionBankItem(
        id="test_doc_001",
        text="Write a join query.",
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=3,
        domains=domains,
        ingestion_metadata=IngestionMetadata(
            source_name="manual_sql_expansion_wave1",
            source_type="question_corpus",
            dataset_version=CORPUS_INDEX_DATASET_VERSION,
            ingestion_timestamp=datetime(1970, 1, 1, tzinfo=timezone.utc),
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="manual_sql_expansion_wave1",
            source_type="question_corpus",
            dataset_version=CORPUS_INDEX_DATASET_VERSION,
        ),
    )


# ----------------------------------------------------------------
# RetrievalCandidate → QuestionBankItem
# ----------------------------------------------------------------

class TestRetrievalCandidateToQuestionBankItem:

    def test_single_domain_propagated(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate("join"))
        assert item.domains == ["join"]

    def test_csv_domains_propagated(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate("join,group_by"))
        assert item.domains == ["join", "group_by"]

    def test_three_domains_propagated(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate("join,group_by,having"))
        assert item.domains == ["join", "group_by", "having"]

    def test_empty_when_no_domains_metadata(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate(None))
        assert item.domains == []

    def test_empty_when_domains_metadata_is_empty_string(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate(""))
        assert item.domains == []


# ----------------------------------------------------------------
# QuestionBankItem → Question (WrittenQuestionMapper)
# ----------------------------------------------------------------

class TestQuestionBankItemToQuestion:

    def test_domains_in_provenance_when_bank_item_has_domains(self) -> None:
        mapper = WrittenQuestionMapper()
        item = _bank_item(["exists"])

        question = mapper.from_bank_item(item)

        assert question.provenance is not None
        assert question.provenance.domains == ["exists"]

    def test_domains_in_provenance_multi(self) -> None:
        mapper = WrittenQuestionMapper()
        item = _bank_item(["group_by", "having"])

        question = mapper.from_bank_item(item)

        assert question.provenance is not None
        assert question.provenance.domains == ["group_by", "having"]

    def test_provenance_domains_empty_when_bank_item_has_no_domains(self) -> None:
        mapper = WrittenQuestionMapper()
        item = _bank_item([])

        question = mapper.from_bank_item(item)

        assert question.provenance is not None
        assert question.provenance.domains == []

    def test_question_provenance_not_mutated_on_original_item(self) -> None:
        mapper = WrittenQuestionMapper()
        item = _bank_item(["join"])

        question = mapper.from_bank_item(item)

        assert question.provenance is not item.provenance


# ----------------------------------------------------------------
# End-to-end: RetrievalCandidate → QuestionBankItem → Question
# ----------------------------------------------------------------

class TestEndToEndDomainPropagation:

    def test_full_chain_single_domain(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate("join"))
        question = WrittenQuestionMapper().from_bank_item(item)

        assert item.domains == ["join"]
        assert question.provenance is not None
        assert question.provenance.domains == ["join"]

    def test_full_chain_multi_domain(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate("group_by,having"))
        question = WrittenQuestionMapper().from_bank_item(item)

        assert item.domains == ["group_by", "having"]
        assert question.provenance is not None
        assert question.provenance.domains == ["group_by", "having"]

    def test_full_chain_no_domain_metadata(self) -> None:
        item = RetrievalCandidateMapper().map_one(_candidate(None))
        question = WrittenQuestionMapper().from_bank_item(item)

        assert item.domains == []
        assert question.provenance is not None
        assert question.provenance.domains == []
