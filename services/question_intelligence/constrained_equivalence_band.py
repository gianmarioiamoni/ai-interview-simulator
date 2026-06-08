# services/question_intelligence/constrained_equivalence_band.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer

DECONVERGENCE_AREAS: frozenset[str] = frozenset(
    {
        "technical_background",
        "technical_technical_knowledge",
        "technical_case_study",
        "technical_coding",
    }
)

EQUIVALENCE_BAND_PCT = 0.05


class ConstrainedEquivalenceBand:

    def __init__(
        self,
        variety_scorer: SessionVarietyScorer | None = None,
        max_allowed_jump: int = 2,
        band_pct: float = EQUIVALENCE_BAND_PCT,
    ) -> None:

        self._variety_scorer = (
            variety_scorer
            if variety_scorer is not None
            else SessionVarietyScorer()
        )
        self._max_allowed_jump = max_allowed_jump
        self._band_pct = band_pct

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

        best_score = self._candidate_score(best)
        floor = self._score_floor(best_score)
        best_tier = self._adaptive_tier(
            candidate=best,
            target=target,
            previous_difficulty=previous_difficulty,
        )

        equivalents = [
            candidate
            for candidate in pool
            if self._candidate_score(candidate) >= floor
            and self._adaptive_tier(
                candidate=candidate,
                target=target,
                previous_difficulty=previous_difficulty,
            )
            == best_tier
        ]

        if len(equivalents) < 2:
            return best

        return self._pick_diversity_best(
            equivalents=equivalents,
            context=context,
            rank_index=rank_index,
            selected_bank_items=selected_bank_items,
        )

    def _pick_diversity_best(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
        selected_bank_items: list[QuestionBankItem],
    ) -> RetrievalCandidate:

        used_ids = self._historical_usage_ids(context)

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

    def _historical_usage_ids(
        self,
        context: AdaptiveRetrievalContext,
    ) -> set[str]:

        return {
            *context.memory.asked_question_ids,
            *context.already_used_question_ids,
        }

    def _candidate_score(
        self,
        candidate: RetrievalCandidate,
    ) -> float:

        return float(candidate.adaptive_score or candidate.final_score)

    def _score_floor(
        self,
        best_score: float,
    ) -> float:

        margin = max(0.01, best_score * self._band_pct)
        return best_score - margin

    def _adaptive_tier(
        self,
        candidate: RetrievalCandidate,
        target: int,
        previous_difficulty: int | None,
    ) -> tuple[int, int]:

        difficulty = self._candidate_difficulty(candidate)

        if difficulty is None:
            return (999, 1)

        target_distance = abs(difficulty - target)
        jump = (
            abs(difficulty - previous_difficulty)
            if previous_difficulty is not None
            else 0
        )
        spike = 0 if jump <= self._max_allowed_jump else 1

        return (target_distance, spike)

    def _candidate_difficulty(
        self,
        candidate: RetrievalCandidate,
    ) -> int | None:

        raw = candidate.document.metadata.get("difficulty")

        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
