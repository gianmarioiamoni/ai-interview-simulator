# tests/services/question_intelligence/test_sql_pipeline_retrieval.py

from datetime import datetime, timezone
from unittest.mock import MagicMock

from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_intelligence.pipelines.sql_pipeline_retrieval import (
    SqlPipelineRetrievalHelper,
)
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy


def _candidate(doc_id: str, text: str) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=text,
            metadata={
                "document_id": doc_id,
                "role": "fullstack_engineer",
                "seniority": "mid",
                "area": "technical_database",
                "difficulty": 3,
                "source": "test",
            },
        ),
        semantic_score=0.9,
        quality_score=0.8,
        final_score=0.85,
        adaptive_score=0.85,
    )


def _bank_item(doc_id: str, text: str):

    from domain.contracts.question.question_bank_item import QuestionBankItem

    return QuestionBankItem(
        id=doc_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.FULLSTACK_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
        ),
    )


def test_sql_retrieval_merges_next_stage_when_pool_shallow() -> None:

    strict_filters = RetrievalFilters(
        role="fullstack_engineer",
        seniority="mid",
        area="technical_database",
    )
    relaxed_filters = RetrievalFilters(area="technical_database")

    chroma = MagicMock()
    chroma.search_with_filters.side_effect = [
        [_candidate("locking-id", "Explain optimistic locking.")],
        [
            _candidate("sql-1", "Write a query to select employees."),
            _candidate("sql-2", "Find rows using a join."),
            _candidate("sql-3", "List departments with indexing."),
        ],
    ]

    repetition_filter = MagicMock()
    repetition_filter.apply.side_effect = lambda candidates, memory: candidates

    policy = MagicMock()
    policy.build_relaxation_stages.return_value = [
        strict_filters,
        relaxed_filters,
    ]

    context_adapter = MagicMock()
    context_adapter.adapt.return_value = MagicMock(
        target_question_count=10,
        memory=InterviewRetrievalMemory(),
    )

    coverage = MagicMock()
    coverage.apply.side_effect = lambda candidates, context: candidates

    weak = MagicMock()
    weak.apply.side_effect = lambda candidates, context: candidates

    mapper = MagicMock()
    mapper.map.side_effect = lambda candidates: [
        _bank_item(
            candidate.document.metadata["document_id"],
            candidate.document.page_content,
        )
        for candidate in candidates
    ]

    helper = SqlPipelineRetrievalHelper(
        context_adapter=context_adapter,
        policy=policy,
        chroma_retrieval=chroma,
        coverage_engine=coverage,
        weak_domain_engine=weak,
        repetition_filter=repetition_filter,
        candidate_mapper=mapper,
    )

    result = helper.retrieve_candidates(
        query="database sql",
        retrieval_strategy=RetrievalStrategy(
            k=10,
            fetch_k=40,
        ),
        role="fullstack_engineer",
        level="mid",
        interview_type="technical",
        area="technical_database",
        memory=InterviewRetrievalMemory(),
    )

    assert len(result) == 4
    assert chroma.search_with_filters.call_count == 2
    assert all(call.kwargs["k"] == 50 for call in chroma.search_with_filters.call_args_list)


def test_sql_retrieval_uses_expanded_fetch_depth() -> None:

    chroma = MagicMock()
    chroma.search_with_filters.return_value = [
        _candidate("sql-1", "Write a query to select employees."),
        _candidate("sql-2", "Find rows using a join."),
        _candidate("sql-3", "List departments with indexing."),
    ]

    repetition_filter = MagicMock()
    repetition_filter.apply.side_effect = lambda candidates, memory: candidates

    policy = MagicMock()
    policy.build_relaxation_stages.return_value = [
        RetrievalFilters(area="technical_database"),
    ]

    context_adapter = MagicMock()
    context_adapter.adapt.return_value = MagicMock(
        target_question_count=10,
        memory=InterviewRetrievalMemory(),
    )

    coverage = MagicMock()
    coverage.apply.side_effect = lambda candidates, context: candidates

    weak = MagicMock()
    weak.apply.side_effect = lambda candidates, context: candidates

    mapper = MagicMock()
    mapper.map.side_effect = lambda candidates: [
        _bank_item(
            candidate.document.metadata["document_id"],
            candidate.document.page_content,
        )
        for candidate in candidates
    ]

    helper = SqlPipelineRetrievalHelper(
        context_adapter=context_adapter,
        policy=policy,
        chroma_retrieval=chroma,
        coverage_engine=coverage,
        weak_domain_engine=weak,
        repetition_filter=repetition_filter,
        candidate_mapper=mapper,
    )

    helper.retrieve_candidates(
        query="database sql",
        retrieval_strategy=RetrievalStrategy(k=10, fetch_k=40),
        role="fullstack_engineer",
        level="mid",
        interview_type="technical",
        area="technical_database",
        memory=InterviewRetrievalMemory(),
    )

    chroma.search_with_filters.assert_called_once()
    assert chroma.search_with_filters.call_args.kwargs["k"] == 50
