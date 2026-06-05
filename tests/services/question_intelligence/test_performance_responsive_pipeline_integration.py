# tests/services/question_intelligence/test_performance_responsive_pipeline_integration.py

from datetime import datetime, timezone
from unittest.mock import MagicMock

from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    AdaptiveRetrievalService,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_intelligence.pipelines.coding_pipeline_retrieval import (
    CodingPipelineRetrievalHelper,
)
from services.question_intelligence.pipelines.sql_pipeline_retrieval import (
    SqlPipelineRetrievalHelper,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy


def _candidate(doc_id: str, difficulty: int, area: str, score: float) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=f"Implement solution {doc_id}",
            metadata={
                "document_id": doc_id,
                "role": "fullstack_engineer",
                "seniority": "mid",
                "area": area,
                "difficulty": difficulty,
                "source": "test",
            },
        ),
        semantic_score=score,
        quality_score=score,
        final_score=score,
        adaptive_score=score,
    )


def _build_context_adapter(target_difficulty: int = 4) -> MagicMock:

    adapter = MagicMock()
    adapter.adapt.return_value = MagicMock(
        target_question_count=3,
        target_difficulty=target_difficulty,
        memory=InterviewRetrievalMemory(difficulty_history=[3]),
    )

    return adapter


def test_adaptive_retrieval_service_prefers_target_difficulty() -> None:

    context = AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area="technical_background",
        target_question_count=1,
        target_difficulty=4,
        memory=InterviewRetrievalMemory(difficulty_history=[3]),
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search_with_filters.return_value = [
        _candidate("top", difficulty=2, area="technical_background", score=0.95),
        _candidate("aligned", difficulty=4, area="technical_background", score=0.70),
        _candidate("hard", difficulty=5, area="technical_background", score=0.80),
    ]

    service = AdaptiveRetrievalService(
        retrieval=mock_retrieval,
        performance_selector=PerformanceResponsiveCandidateSelector(),
    )

    results = service.retrieve(
        query="background",
        context=context,
    )

    assert results[0].document.metadata["document_id"] == "aligned"


def test_coding_retrieval_helper_prioritizes_target_difficulty() -> None:

    chroma = MagicMock()
    chroma.search_with_filters.return_value = [
        _candidate("coding-top", difficulty=2, area="technical_coding", score=0.95),
        _candidate("coding-aligned", difficulty=4, area="technical_coding", score=0.70),
        _candidate("coding-hard", difficulty=5, area="technical_coding", score=0.80),
    ]

    repetition_filter = MagicMock()
    repetition_filter.apply.side_effect = lambda candidates, memory: candidates

    policy = MagicMock()
    policy.build_relaxation_stages.return_value = [
        RetrievalFilters(area="technical_coding"),
    ]

    coverage = MagicMock()
    coverage.apply.side_effect = lambda candidates, context: candidates

    weak = MagicMock()
    weak.apply.side_effect = lambda candidates, context: candidates

    from domain.contracts.question.question_bank_item import QuestionBankItem

    mapper = MagicMock()
    mapper.map.side_effect = lambda candidates: [
        QuestionBankItem(
            id=candidate.document.metadata["document_id"],
            text=candidate.document.page_content,
            interview_type=InterviewType.TECHNICAL,
            role=Role(type=RoleType.FULLSTACK_ENGINEER),
            area=InterviewArea.TECH_CODING,
            level=SeniorityLevel.MID,
            difficulty=candidate.document.metadata["difficulty"],
            ingestion_metadata=IngestionMetadata(
                source_name="test",
                source_type="question_corpus",
                dataset_version="v1",
                ingestion_timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
            ),
        )
        for candidate in candidates
    ]

    helper = CodingPipelineRetrievalHelper(
        context_adapter=_build_context_adapter(target_difficulty=4),
        policy=policy,
        chroma_retrieval=chroma,
        coverage_engine=coverage,
        weak_domain_engine=weak,
        repetition_filter=repetition_filter,
        candidate_mapper=mapper,
        performance_selector=PerformanceResponsiveCandidateSelector(),
    )

    result = helper.retrieve_candidates(
        query="coding",
        retrieval_strategy=RetrievalStrategy(k=3, fetch_k=9),
        role="fullstack_engineer",
        level="mid",
        interview_type="technical",
        area="technical_coding",
        memory=InterviewRetrievalMemory(),
    )

    assert result[0].id == "coding-aligned"


def test_sql_retrieval_helper_prioritizes_target_difficulty() -> None:

    chroma = MagicMock()
    chroma.search_with_filters.return_value = [
        _candidate("sql-top", difficulty=2, area="technical_database", score=0.95),
        _candidate("sql-aligned", difficulty=4, area="technical_database", score=0.70),
        _candidate("sql-hard", difficulty=5, area="technical_database", score=0.80),
    ]

    repetition_filter = MagicMock()
    repetition_filter.apply.side_effect = lambda candidates, memory: candidates

    policy = MagicMock()
    policy.build_relaxation_stages.return_value = [
        RetrievalFilters(area="technical_database"),
    ]

    coverage = MagicMock()
    coverage.apply.side_effect = lambda candidates, context: candidates

    weak = MagicMock()
    weak.apply.side_effect = lambda candidates, context: candidates

    from domain.contracts.question.question_bank_item import QuestionBankItem

    mapper = MagicMock()
    mapper.map.side_effect = lambda candidates: [
        QuestionBankItem(
            id=candidate.document.metadata["document_id"],
            text=candidate.document.page_content,
            interview_type=InterviewType.TECHNICAL,
            role=Role(type=RoleType.FULLSTACK_ENGINEER),
            area=InterviewArea.TECH_DATABASE,
            level=SeniorityLevel.MID,
            difficulty=candidate.document.metadata["difficulty"],
            ingestion_metadata=IngestionMetadata(
                source_name="test",
                source_type="question_corpus",
                dataset_version="v1",
                ingestion_timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
            ),
        )
        for candidate in candidates
    ]

    helper = SqlPipelineRetrievalHelper(
        context_adapter=_build_context_adapter(target_difficulty=4),
        policy=policy,
        chroma_retrieval=chroma,
        coverage_engine=coverage,
        weak_domain_engine=weak,
        repetition_filter=repetition_filter,
        candidate_mapper=mapper,
        performance_selector=PerformanceResponsiveCandidateSelector(),
    )

    result = helper.retrieve_candidates(
        query="sql",
        retrieval_strategy=RetrievalStrategy(k=3, fetch_k=9),
        role="fullstack_engineer",
        level="mid",
        interview_type="technical",
        area="technical_database",
        memory=InterviewRetrievalMemory(),
    )

    assert result[0].id == "sql-aligned"
