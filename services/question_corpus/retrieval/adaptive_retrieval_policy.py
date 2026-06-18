# services/question_corpus/retrieval/adaptive_retrieval_policy.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters

# Progressive seniority widening: maps a seniority level to ordered widening stages.
# Each inner list represents the allowed seniority values at that relaxation stage.
_SENIORITY_WIDENING: dict[str, list[str | None]] = {
    "junior": ["junior", "junior", "junior", "junior"],
    "mid": ["mid", "mid", "mid", "mid"],
    "senior": ["senior", "senior", "senior,mid", "senior,mid"],
    "staff": ["staff", "staff", "staff,senior", "staff,senior"],
}

_WIDENING_SEPARATOR = ","


def _widened_seniority(seniority: str, stage: int) -> str | None:
    stages = _SENIORITY_WIDENING.get(seniority.lower())
    if stages is None:
        return seniority
    return stages[min(stage, len(stages) - 1)]


class AdaptiveRetrievalPolicy:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build_filters(
        self,
        context: AdaptiveRetrievalContext,
    ) -> RetrievalFilters:

        return RetrievalFilters(
            role=context.current_role,
            seniority=context.seniority,
            area=context.target_area,
            min_difficulty=self._min_difficulty(
                context,
            ),
            max_difficulty=self._max_difficulty(
                context,
            ),
        )

    def build_relaxation_stages(
        self,
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalFilters]:

        min_difficulty = self._min_difficulty(context)
        max_difficulty = self._max_difficulty(context)
        target_area = context.target_area
        seniority = context.seniority

        return [
            RetrievalFilters(
                role=context.current_role,
                seniority=_widened_seniority(seniority, 0),
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
                seniority=_widened_seniority(seniority, 1),
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
                seniority=_widened_seniority(seniority, 2),
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
                seniority=_widened_seniority(seniority, 3),
                area=target_area,
            ),
        ]

    # =====================================================
    # INTERNALS
    # =====================================================

    def _min_difficulty(
        self,
        context: AdaptiveRetrievalContext,
    ) -> int | None:

        if context.target_difficulty is None:
            return None

        return max(
            1,
            context.target_difficulty - 1,
        )

    def _max_difficulty(
        self,
        context: AdaptiveRetrievalContext,
    ) -> int | None:

        if context.target_difficulty is None:
            return None

        return min(
            5,
            context.target_difficulty + 1,
        )
