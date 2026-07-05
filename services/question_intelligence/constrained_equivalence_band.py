# services/question_intelligence/constrained_equivalence_band.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer
from services.question_intelligence.equivalence_band_scoring import (
    adaptive_tier,
    candidate_score,
    historical_usage_ids,
    score_floor,
)
from services.question_intelligence.cross_interview_pick_tracker import (
    CrossInterviewPickTracker,
)
from services.question_intelligence.fresh_start_selection_strategy import (
    FreshStartSelectionStrategy,
    CANONICAL_FRESH_START_AREAS,
)

DECONVERGENCE_AREAS: frozenset[str] = frozenset(
    {
        "technical_background",
        "technical_technical_knowledge",
        "technical_case_study",
        "technical_coding",
        "technical_database",
    }
)

EQUIVALENCE_BAND_PCT = 0.05

FRESH_START_MAX_TARGET_DISTANCE = 1

KNOWLEDGE_FRESH_START_AREA = "technical_technical_knowledge"

# Module-level tracker instance — owns the cross-interview pick counts.
_TRACKER = CrossInterviewPickTracker()

# Public alias pointing at the tracker's live internal dict (used by tests and scripts).
_CROSS_INTERVIEW_PICK_COUNTS: dict[str, int] = _TRACKER.counts


def reset_cross_interview_pick_counts() -> None:
    _TRACKER.reset()


class ConstrainedEquivalenceBand:

    def __init__(
        self,
        variety_scorer: SessionVarietyScorer | None = None,
        topic_extractor: TopicExtractor | None = None,
        max_allowed_jump: int = 2,
        band_pct: float = EQUIVALENCE_BAND_PCT,
    ) -> None:

        self._variety_scorer = (
            variety_scorer
            if variety_scorer is not None
            else SessionVarietyScorer()
        )
        self._topic_extractor = (
            topic_extractor
            if topic_extractor is not None
            else TopicExtractor()
        )
        self._max_allowed_jump = max_allowed_jump
        self._band_pct = band_pct

        self._fresh_start_strategy = FreshStartSelectionStrategy(
            variety_scorer=self._variety_scorer,
            topic_extractor=self._topic_extractor,
            max_allowed_jump=self._max_allowed_jump,
            tracker=_TRACKER,
        )

    def is_eligible(self, target_area: str) -> bool:

        return target_area in DECONVERGENCE_AREAS

    def diversify_pick(
        self,
        pool: list[RetrievalCandidate],
        best: RetrievalCandidate,
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
        selected_bank_items: list[QuestionBankItem],
    ) -> RetrievalCandidate:

        if not self.is_eligible(context.target_area):
            return best

        band_anchor = best

        if (
            self._is_fresh_start(
                context=context,
                selected_bank_items=selected_bank_items,
            )
            and context.target_area in CANONICAL_FRESH_START_AREAS
        ):
            band_anchor = max(
                pool,
                key=lambda candidate: candidate_score(candidate),
            )

        best_tier = adaptive_tier(
            candidate=band_anchor,
            target=target,
            previous_difficulty=previous_difficulty,
            max_allowed_jump=self._max_allowed_jump,
        )

        equivalents = self._collect_equivalents(
            pool=pool,
            best=band_anchor,
            best_tier=best_tier,
            target=target,
            previous_difficulty=previous_difficulty,
            context=context,
            selected_bank_items=selected_bank_items,
        )

        if len(equivalents) < 2:
            return best

        return self._pick_diversity_best(
            equivalents=equivalents,
            context=context,
            rank_index=rank_index,
            selected_bank_items=selected_bank_items,
        )

    def _collect_equivalents(
        self,
        pool: list[RetrievalCandidate],
        best: RetrievalCandidate,
        best_tier: tuple[int, int],
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> list[RetrievalCandidate]:

        tier_matches = [
            candidate
            for candidate in pool
            if self._matches_adaptive_tier(
                candidate=candidate,
                best_tier=best_tier,
                target=target,
                previous_difficulty=previous_difficulty,
                context=context,
                selected_bank_items=selected_bank_items,
            )
        ]

        if not tier_matches:
            return []

        fresh = self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        )

        if fresh:
            return tier_matches

        anchor_score = candidate_score(best)
        floor = score_floor(anchor_score, self._band_pct)

        return [
            candidate
            for candidate in tier_matches
            if candidate_score(candidate) >= floor
        ]

    def _matches_adaptive_tier(
        self,
        candidate: RetrievalCandidate,
        best_tier: tuple[int, int],
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> bool:

        tier = adaptive_tier(
            candidate=candidate,
            target=target,
            previous_difficulty=previous_difficulty,
            max_allowed_jump=self._max_allowed_jump,
        )

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            return (
                tier[0] <= FRESH_START_MAX_TARGET_DISTANCE
                and tier[1] == best_tier[1]
            )

        return tier == best_tier

    def _pick_diversity_best(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
        selected_bank_items: list[QuestionBankItem],
    ) -> RetrievalCandidate:

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            return self._fresh_start_strategy.pick(
                equivalents=equivalents,
                context=context,
            )

        used_ids = historical_usage_ids(context)

        def diversity_key(candidate: RetrievalCandidate) -> tuple:

            document_id = str(candidate.document.metadata.get("document_id", ""))
            historical = 1 if document_id in used_ids else 0
            variety = self._variety_scorer.variety_penalty_tuple(
                candidate=candidate,
                context=context,
                selected_bank_items=selected_bank_items,
            )
            novelty = -self._variety_scorer.apply_novelty_scoring(
                candidate=candidate,
                selected_bank_items=selected_bank_items,
            )

            return (historical, *variety, novelty, rank_index[id(candidate)])

        equivalents.sort(key=diversity_key)
        return equivalents[0]

    def _is_fresh_start(
        self,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> bool:

        if selected_bank_items:
            return False

        if context.already_used_question_ids:
            return False

        memory = context.memory

        return (
            not memory.asked_question_ids
            and not memory.session_selected_prompts
            and not memory.session_used_topics
            and not memory.difficulty_history
        )

    # ------------------------------------------------------------------
    # COMPAT SHIM — tests call _pick_fresh_start_equivalent directly
    # on the band instance; delegate to the strategy unchanged.
    # ------------------------------------------------------------------

    def _pick_fresh_start_equivalent(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> RetrievalCandidate:
        return self._fresh_start_strategy.pick(
            equivalents=equivalents,
            context=context,
        )

    # ------------------------------------------------------------------
    # COMPAT SHIMS — delegate to equivalence_band_scoring module
    # ------------------------------------------------------------------

    def _score_floor(self, best_score: float) -> float:
        return score_floor(best_score, self._band_pct)

    def _adaptive_tier(
        self,
        candidate: RetrievalCandidate,
        target: int,
        previous_difficulty: int | None,
    ) -> tuple[int, int]:
        return adaptive_tier(
            candidate=candidate,
            target=target,
            previous_difficulty=previous_difficulty,
            max_allowed_jump=self._max_allowed_jump,
        )
