# tests/services/question_intelligence/test_constrained_equivalence_selection.py

from langchain_core.documents import Document

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.constrained_equivalence_band import (
    DECONVERGENCE_AREAS,
    EQUIVALENCE_BAND_PCT,
    ConstrainedEquivalenceBand,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer


def _context(
    target_area: str = "technical_technical_knowledge",
    target_difficulty: int = 4,
    difficulty_history: list[int] | None = None,
    asked_question_ids: list[str] | None = None,
    session_selected_prompts: list[str] | None = None,
    session_used_topics: list[str] | None = None,
    retrieval_query: str | None = None,
) -> AdaptiveRetrievalContext:

    return AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area=target_area,
        target_question_count=1,
        target_difficulty=target_difficulty,
        retrieval_query=retrieval_query,
        memory=InterviewRetrievalMemory(
            difficulty_history=difficulty_history or [],
            asked_question_ids=asked_question_ids or [],
            session_selected_prompts=session_selected_prompts or [],
            session_used_topics=session_used_topics or [],
        ),
    )


def _candidate(
    doc_id: str,
    difficulty: int,
    score: float,
    prompt: str | None = None,
    area: str = "technical_technical_knowledge",
) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=prompt or f"Question about {doc_id} topic",
            metadata={
                "document_id": doc_id,
                "difficulty": difficulty,
                "area": area,
            },
        ),
        semantic_score=score,
        quality_score=score,
        final_score=score,
        adaptive_score=score,
    )


def test_equivalence_band_uses_five_percent_threshold() -> None:

    assert EQUIVALENCE_BAND_PCT == 0.05

    band = ConstrainedEquivalenceBand()
    floor = band._score_floor(0.90)

    assert floor == 0.855


def test_deconvergence_areas_include_database() -> None:

    assert "technical_database" in DECONVERGENCE_AREAS
    assert "technical_coding" in DECONVERGENCE_AREAS


def test_selects_adaptive_best_when_no_equivalents() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("best", difficulty=4, score=0.95),
        _candidate("far-score", difficulty=4, score=0.50),
        _candidate("far-diff", difficulty=2, score=0.94),
    ]

    selected = selector.select(pool=pool, context=_context(target_difficulty=4))

    assert selected[0].document.metadata["document_id"] == "best"


def test_diversifies_among_adaptive_equivalents_in_band() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("used-before", difficulty=4, score=0.95, prompt="Explain caching layers"),
        _candidate("fresh-topic", difficulty=4, score=0.94, prompt="Describe message queue patterns"),
        _candidate("outside-band", difficulty=4, score=0.70, prompt="Other topic entirely"),
    ]
    context = _context(
        target_difficulty=4,
        asked_question_ids=["used-before"],
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "fresh-topic"


def test_preserves_adaptive_difficulty_over_diversity() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("high-score-wrong-diff", difficulty=2, score=0.99),
        _candidate("target-diff", difficulty=4, score=0.90),
        _candidate("alt-target", difficulty=4, score=0.89),
    ]

    selected = selector.select(pool=pool, context=_context(target_difficulty=4))

    assert selected[0].document.metadata["document_id"] in {"target-diff", "alt-target"}
    assert selected[0].document.metadata["difficulty"] == 4


def test_preserves_progression_constraints() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("spike", difficulty=5, score=0.95),
        _candidate("smooth-a", difficulty=4, score=0.94),
        _candidate("smooth-b", difficulty=4, score=0.93),
    ]
    context = _context(
        target_difficulty=4,
        difficulty_history=[3],
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] in {"smooth-a", "smooth-b"}


def test_database_area_applies_deconvergence_via_prioritize() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate(
            "used",
            difficulty=4,
            score=0.95,
            prompt="SELECT users FROM employees",
            area="technical_database",
        ),
        _candidate(
            "fresh",
            difficulty=4,
            score=0.94,
            prompt="JOIN orders ON customers",
            area="technical_database",
        ),
    ]
    context = _context(
        target_area="technical_database",
        target_difficulty=4,
        asked_question_ids=["used"],
    )

    prioritized = selector.prioritize(pool=pool, context=context)

    assert prioritized[0].document.metadata["document_id"] == "fresh"


def test_coding_area_applies_deconvergence_via_prioritize() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate(
            "used",
            difficulty=4,
            score=0.95,
            prompt="Implement binary search tree",
            area="technical_coding",
        ),
        _candidate(
            "fresh",
            difficulty=4,
            score=0.94,
            prompt="Implement graph traversal",
            area="technical_coding",
        ),
    ]
    context = _context(
        target_area="technical_coding",
        target_difficulty=4,
        asked_question_ids=["used"],
    )

    prioritized = selector.prioritize(pool=pool, context=context)

    assert prioritized[0].document.metadata["document_id"] == "fresh"


def test_session_prompt_penalty_breaks_equivalence_tie() -> None:

    selector = PerformanceResponsiveCandidateSelector(
        variety_scorer=SessionVarietyScorer(),
    )
    pool = [
        _candidate(
            "repeat-prompt",
            difficulty=4,
            score=0.95,
            prompt="Explain REST API design principles and versioning",
        ),
        _candidate(
            "fresh-prompt",
            difficulty=4,
            score=0.94,
            prompt="Design a distributed cache invalidation strategy",
        ),
    ]
    context = _context(
        target_difficulty=4,
        session_selected_prompts=[
            "Explain REST API design principles and versioning strategy",
        ],
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "fresh-prompt"


def test_single_candidate_fallback_unchanged() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [_candidate("only", difficulty=4, score=0.80)]

    selected = selector.select(pool=pool, context=_context(target_difficulty=4))

    assert selected == pool


def test_fresh_start_rotates_among_equivalents_by_role_and_query() -> None:

    band = ConstrainedEquivalenceBand()
    equivalents = [
        _candidate("doc-a", difficulty=4, score=0.95, prompt="SELECT from users"),
        _candidate("doc-b", difficulty=4, score=0.94, prompt="JOIN orders on customers"),
        _candidate("doc-c", difficulty=4, score=0.93, prompt="GROUP BY department"),
    ]
    roles = [
        "backend_engineer",
        "data_engineer",
        "frontend_engineer",
        "devops_engineer",
        "ml_engineer",
    ]
    picks = set()

    for index, role in enumerate(roles):
        context = _context(
            target_area="technical_database",
            target_difficulty=4,
        ).model_copy(
            update={
                "current_role": role,
                "seniority": ["junior", "mid", "senior"][index % 3],
                "retrieval_query": f"{role} SQL interview question variant {index}",
            },
        )
        pick = band._pick_fresh_start_equivalent(
            equivalents=equivalents,
            context=context,
        )
        picks.add(pick.document.metadata["document_id"])

    assert picks.issubset({"doc-a", "doc-b", "doc-c"})
    assert len(picks) >= 2


def test_fresh_start_falls_back_to_session_behavior_when_memory_populated() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate(
            "used-before",
            difficulty=4,
            score=0.95,
            prompt="Explain indexing strategies",
            area="technical_database",
        ),
        _candidate(
            "fresh-topic",
            difficulty=4,
            score=0.94,
            prompt="Describe transaction isolation levels",
            area="technical_database",
        ),
    ]
    context = _context(
        target_area="technical_database",
        target_difficulty=4,
        asked_question_ids=["used-before"],
        retrieval_query="SQL transactions interview question",
    )

    selected = selector.select(pool=pool, context=context)

    assert selected[0].document.metadata["document_id"] == "fresh-topic"


def test_missing_target_difficulty_preserves_rank_order() -> None:

    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("first", difficulty=4, score=0.95),
        _candidate("second", difficulty=4, score=0.94),
    ]

    selected = selector.select(pool=pool, context=_context(target_difficulty=None))

    assert selected[0].document.metadata["document_id"] == "first"
