# tests/services/question_intelligence/test_performance_responsive_candidate_selector.py

from langchain_core.documents import Document

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)


def _context(
    target_difficulty: int | None = 4,
    difficulty_history: list[int] | None = None,
    target_question_count: int = 1,
    asked_question_ids: list[str] | None = None,
    target_area: str = "technical_technical_knowledge",
) -> AdaptiveRetrievalContext:

    return AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area=target_area,
        target_question_count=target_question_count,
        target_difficulty=target_difficulty,
        memory=InterviewRetrievalMemory(
            difficulty_history=difficulty_history or [],
            asked_question_ids=asked_question_ids or [],
        ),
    )


def _candidate(doc_id: str, difficulty: int, score: float) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=f"Question {doc_id}",
            metadata={
                "document_id": doc_id,
                "difficulty": difficulty,
            },
        ),
        semantic_score=score,
        quality_score=score,
        final_score=score,
        adaptive_score=score,
    )


def test_selects_closest_difficulty_over_top_ranked() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("top-ranked", difficulty=2, score=0.95),
        _candidate("closest", difficulty=4, score=0.70),
        _candidate("far", difficulty=5, score=0.80),
    ]

    # Non-fresh-start context: strict tier matching applies so exact difficulty
    # match wins regardless of score.
    selected = selector.select(
        pool=pool,
        context=_context(
            target_difficulty=4,
            target_area="technical_case_study",
            asked_question_ids=["prior-question"],
        ),
    )

    assert len(selected) == 1
    assert selected[0].document.metadata["document_id"] == "closest"


def test_preserves_progression_when_target_equally_close() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("spike", difficulty=5, score=0.95),
        _candidate("smooth", difficulty=4, score=0.90),
    ]
    context = _context(
        target_difficulty=4,
        difficulty_history=[3],
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "smooth"


def test_uses_ranking_as_tie_breaker_for_equal_target_distance() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("rank-1", difficulty=3, score=0.95),
        _candidate("rank-2", difficulty=5, score=0.70),
    ]
    context = _context(
        target_difficulty=4,
        asked_question_ids=["prior"],
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "rank-1"


def test_single_candidate_fallback_preserves_behavior() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [_candidate("only", difficulty=3, score=0.50)]

    selected = selector.select(pool=pool, context=_context(target_difficulty=5))

    assert selected == pool


def test_missing_target_difficulty_falls_back_to_rank_order() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("first", difficulty=2, score=0.95),
        _candidate("second", difficulty=5, score=0.50),
    ]
    context = _context(target_difficulty=None)

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "first"


def test_prioritize_reorders_scan_pool_for_coding_sql_paths() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("top", difficulty=2, score=0.99),
        _candidate("target", difficulty=4, score=0.60),
        _candidate("other", difficulty=5, score=0.80),
    ]

    # Non-fresh-start: strict tier matching ensures exact difficulty match wins.
    prioritized = selector.prioritize(
        pool=pool,
        context=_context(
            target_difficulty=4,
            target_area="technical_case_study",
            asked_question_ids=["prior-question"],
        ),
    )

    assert prioritized[0].document.metadata["document_id"] == "target"


def test_written_path_selects_multiple_with_progression() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("q1", difficulty=3, score=0.95),
        _candidate("q2", difficulty=4, score=0.90),
        _candidate("q3", difficulty=5, score=0.85),
    ]
    context = _context(
        target_difficulty=4,
        target_question_count=2,
        asked_question_ids=["prior"],
    )

    selected = selector.select(pool=pool, context=context)

    assert len(selected) == 2
    assert selected[0].document.metadata["document_id"] == "q2"
    assert selected[1].document.metadata["document_id"] in {"q1", "q3"}
