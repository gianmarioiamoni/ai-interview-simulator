# services/question_corpus/retrieval/adaptive_retrieval_policy.py

from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters


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

        min_difficulty = self._min_difficulty(
            context,
        )

        max_difficulty = self._max_difficulty(
            context,
        )

        target_area = context.target_area

        return [
            RetrievalFilters(
                role=context.current_role,
                seniority=context.seniority,
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
                seniority=context.seniority,
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
                area=target_area,
                min_difficulty=min_difficulty,
                max_difficulty=max_difficulty,
            ),
            RetrievalFilters(
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
