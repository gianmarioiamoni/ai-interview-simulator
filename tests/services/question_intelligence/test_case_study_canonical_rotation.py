# tests/services/question_intelligence/test_case_study_canonical_rotation.py
#
# Phase 7D-C1 — Validates that technical_case_study uses the canonical
# cross-interview rotation path, not deterministic hash ordering.

import pytest

from langchain_core.documents import Document

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.constrained_equivalence_band import (
    CANONICAL_FRESH_START_AREAS,
    ConstrainedEquivalenceBand,
    _CROSS_INTERVIEW_PICK_COUNTS,
    reset_cross_interview_pick_counts,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_cross_interview_pick_counts()


def _fresh_context(
    *,
    role: str = "backend_engineer",
    seniority: str = "senior",
    target_difficulty: int = 3,
    already_used: list[str] | None = None,
    retrieval_query: str = "system design case study",
) -> AdaptiveRetrievalContext:
    ctx = AdaptiveRetrievalContext(
        current_role=role,
        seniority=seniority,
        target_area="technical_case_study",
        target_question_count=1,
        target_difficulty=target_difficulty,
        retrieval_query=retrieval_query,
        memory=InterviewRetrievalMemory(),
    )
    if already_used:
        return ctx.model_copy(update={"already_used_question_ids": already_used})
    return ctx


def _candidate(doc_id: str, difficulty: int = 3, score: float = 0.90) -> RetrievalCandidate:
    return RetrievalCandidate(
        document=Document(
            page_content=f"Case study question for {doc_id}",
            metadata={
                "document_id": doc_id,
                "difficulty": difficulty,
                "area": "technical_case_study",
            },
        ),
        semantic_score=score,
        quality_score=score,
        final_score=score,
        adaptive_score=score,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. technical_case_study is now in CANONICAL_FRESH_START_AREAS
# ─────────────────────────────────────────────────────────────────────────────

def test_case_study_in_canonical_fresh_start_areas() -> None:
    assert "technical_case_study" in CANONICAL_FRESH_START_AREAS


# ─────────────────────────────────────────────────────────────────────────────
# 2. Pick counts are updated after each selection
# ─────────────────────────────────────────────────────────────────────────────

def test_pick_counts_updated_for_case_study() -> None:
    band = ConstrainedEquivalenceBand()
    equivalents = [
        _candidate("cs-a", score=0.95),
        _candidate("cs-b", score=0.94),
        _candidate("cs-c", score=0.93),
    ]
    context = _fresh_context()

    for _ in range(3):
        band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)

    total_picks = sum(_CROSS_INTERVIEW_PICK_COUNTS.values())
    assert total_picks == 3


# ─────────────────────────────────────────────────────────────────────────────
# 3. Repeated fresh-start runs rotate winners (effective depth > 1)
# ─────────────────────────────────────────────────────────────────────────────

def test_repeated_fresh_starts_rotate_winner_across_case_study() -> None:
    band = ConstrainedEquivalenceBand()
    equivalents = [
        _candidate("cs-a", score=0.95),
        _candidate("cs-b", score=0.94),
        _candidate("cs-c", score=0.93),
    ]
    context = _fresh_context()
    winners: set[str] = set()

    for _ in range(10):
        pick = band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)
        winners.add(pick.document.metadata["document_id"])

    assert len(winners) > 1, (
        f"Expected rotation across candidates, got only: {winners}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Deterministic hash branch is NOT used for case study
#    (canonical path does not read rotation_index for the winner selection)
# ─────────────────────────────────────────────────────────────────────────────

def test_case_study_does_not_use_deterministic_hash_branch() -> None:
    band = ConstrainedEquivalenceBand()
    equivalents = [
        _candidate("cs-a", score=0.95),
        _candidate("cs-b", score=0.94),
    ]
    context = _fresh_context()

    first_pick = band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)
    reset_cross_interview_pick_counts()
    second_pick = band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)

    assert first_pick.document.metadata["document_id"] == second_pick.document.metadata["document_id"], (
        "After reset, canonical rotation should restart from zero-count — "
        "same result expected on identical state, but it must be driven by counts, not hash"
    )

    # Drive counts up: second doc should become preferred
    _CROSS_INTERVIEW_PICK_COUNTS[first_pick.document.metadata["document_id"]] = 5
    third_pick = band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)

    other_id = next(
        c.document.metadata["document_id"]
        for c in equivalents
        if c.document.metadata["document_id"] != first_pick.document.metadata["document_id"]
    )
    assert third_pick.document.metadata["document_id"] == other_id, (
        "After inflating pick count, canonical rotation should prefer the other candidate"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Existing canonical areas (background, knowledge, database) unchanged
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("area", [
    "technical_background",
    "technical_technical_knowledge",
    "technical_database",
])
def test_existing_canonical_areas_still_in_set(area: str) -> None:
    assert area in CANONICAL_FRESH_START_AREAS


@pytest.mark.parametrize("area", [
    "technical_background",
    "technical_technical_knowledge",
    "technical_database",
])
def test_existing_canonical_areas_still_update_pick_counts(area: str) -> None:
    band = ConstrainedEquivalenceBand()
    equivalents = [
        _candidate("doc-x", score=0.95),
        _candidate("doc-y", score=0.94),
    ]
    context = AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area=area,
        target_question_count=1,
        target_difficulty=3,
        retrieval_query="interview question",
        memory=InterviewRetrievalMemory(),
    )

    band._pick_fresh_start_equivalent(equivalents=equivalents, context=context)

    total = sum(_CROSS_INTERVIEW_PICK_COUNTS.values())
    assert total == 1


def test_selector_selects_distinct_case_study_docs_over_runs() -> None:
    selector = PerformanceResponsiveCandidateSelector()
    pool = [
        _candidate("cs-a", difficulty=3, score=0.95),
        _candidate("cs-b", difficulty=3, score=0.94),
        _candidate("cs-c", difficulty=3, score=0.93),
        _candidate("cs-d", difficulty=3, score=0.92),
    ]
    winners: set[str] = set()

    for _ in range(12):
        context = _fresh_context()
        selected = selector.select(pool=pool, context=context)
        winners.add(selected[0].document.metadata["document_id"])

    assert len(winners) > 1, (
        f"PerformanceResponsiveCandidateSelector should rotate case-study winners. Got: {winners}"
    )
