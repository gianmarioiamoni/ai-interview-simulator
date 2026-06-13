# services/question_intelligence/fresh_start_selection_strategy.py

"""
Fresh-start selection strategy for ConstrainedEquivalenceBand.

Owns the two sub-strategies used when no session history exists:

  1. Canonical rotation  — for CANONICAL_FRESH_START_AREAS
     Picks the least-used document across interviews by reading/writing
     cross_interview_pick_counts.

  2. Hash rotation       — for all other DECONVERGENCE_AREAS
     Selects deterministically via SHA-256(role|level|theme|query) so the
     same input profile always reaches the same topic bucket.

Both paths delegate primitive scoring to equivalence_band_scoring helpers.
"""

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer
from services.question_intelligence.equivalence_band_scoring import (
    adaptive_tier,
    candidate_score,
    historical_usage_ids,
    rotation_index,
)

CANONICAL_FRESH_START_AREAS: frozenset[str] = frozenset(
    {
        "technical_technical_knowledge",
        "technical_background",
        "technical_database",
        "technical_case_study",
    }
)


class FreshStartSelectionStrategy:
    """
    Picks the best candidate from a fresh-start equivalence set.

    Dependencies are injected explicitly — no hidden module coupling.
    cross_interview_pick_counts is passed by reference so the caller
    (ConstrainedEquivalenceBand) retains ownership of the global dict
    for R5C state extraction.
    """

    def __init__(
        self,
        variety_scorer: SessionVarietyScorer,
        topic_extractor: TopicExtractor,
        max_allowed_jump: int,
        cross_interview_pick_counts: dict[str, int],
    ) -> None:
        self._variety_scorer = variety_scorer
        self._topic_extractor = topic_extractor
        self._max_allowed_jump = max_allowed_jump
        self._cross_interview_pick_counts = cross_interview_pick_counts

    def pick(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> RetrievalCandidate:
        """Select one candidate from a fresh-start equivalence set."""

        if len(equivalents) == 1:
            return equivalents[0]

        theme = get_interview_theme_anchor(context.memory) or ""
        query = context.retrieval_query or ""
        seed = f"{context.current_role}|{context.seniority}|{theme}|{query}"
        used_ids = historical_usage_ids(context)
        target = context.target_difficulty or 3
        previous_difficulty = (
            context.memory.difficulty_history[-1]
            if context.memory.difficulty_history
            else None
        )

        if context.target_area in CANONICAL_FRESH_START_AREAS:
            pick = self._pick_canonical(
                equivalents=equivalents,
                used_ids=used_ids,
            )
        else:
            pick = self._pick_hash_rotation(
                equivalents=equivalents,
                context=context,
                seed=seed,
                used_ids=used_ids,
                target=target,
                previous_difficulty=previous_difficulty,
            )

        document_id = str(pick.document.metadata.get("document_id", ""))

        if context.target_area in CANONICAL_FRESH_START_AREAS and document_id:
            self._cross_interview_pick_counts[document_id] = (
                self._cross_interview_pick_counts.get(document_id, 0) + 1
            )

        return pick

    # ------------------------------------------------------------------
    # CANONICAL PATH
    # ------------------------------------------------------------------

    def _pick_canonical(
        self,
        equivalents: list[RetrievalCandidate],
        used_ids: set[str],
    ) -> RetrievalCandidate:
        """
        Select the candidate with the lowest cross-interview pick count,
        breaking ties by historical usage → score desc → doc_id lexicographic.
        """

        def canonical_tie_break_key(candidate: RetrievalCandidate) -> tuple:
            document_id = str(candidate.document.metadata.get("document_id", ""))
            historical = 1 if document_id in used_ids else 0

            return (
                historical,
                self._cross_interview_pick_counts.get(document_id, 0),
                -candidate_score(candidate),
                document_id,
            )

        return min(equivalents, key=canonical_tie_break_key)

    # ------------------------------------------------------------------
    # HASH-ROTATION PATH
    # ------------------------------------------------------------------

    def _pick_hash_rotation(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
        seed: str,
        used_ids: set[str],
        target: int,
        previous_difficulty: int | None,
    ) -> RetrievalCandidate:
        """
        Deterministic rotation: group by prefix key, select a topic bucket via
        SHA-256 seed, then apply a final deterministic tie-break.
        """

        def prefix_key(candidate: RetrievalCandidate) -> tuple:
            document_id = str(candidate.document.metadata.get("document_id", ""))
            tier = adaptive_tier(
                candidate=candidate,
                target=target,
                previous_difficulty=previous_difficulty,
                max_allowed_jump=self._max_allowed_jump,
            )
            historical = 1 if document_id in used_ids else 0
            variety = self._variety_scorer.variety_penalty_tuple(
                candidate=candidate,
                context=context,
                selected_bank_items=[],
            )

            return (historical, tier[0], tier[1], *variety)

        best_prefix = min(prefix_key(c) for c in equivalents)
        bucket = [c for c in equivalents if prefix_key(c) == best_prefix]

        if len(bucket) > 1:
            topics_in_bucket = list(
                dict.fromkeys(
                    self._topic_extractor.extract(c.document.page_content.strip())
                    for c in bucket
                )
            )

            if len(topics_in_bucket) > 1:
                topic_index = rotation_index(seed, len(topics_in_bucket))
                target_topic = topics_in_bucket[topic_index]
                bucket = [
                    c
                    for c in bucket
                    if self._topic_extractor.extract(c.document.page_content.strip())
                    == target_topic
                ]

        def tie_break_key(candidate: RetrievalCandidate) -> tuple:
            document_id = str(candidate.document.metadata.get("document_id", ""))

            return (
                rotation_index(f"{seed}|{document_id}", 10_000),
                -candidate_score(candidate),
                document_id,
            )

        return min(bucket, key=tie_break_key)
