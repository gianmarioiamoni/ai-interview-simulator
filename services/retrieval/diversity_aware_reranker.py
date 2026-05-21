# services/retrieval/diversity_aware_reranker.py

from collections import defaultdict

from services.retrieval.contracts import (
    HybridRetrievalResult,
)


class DiversityAwareReranker:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        diversity_penalty: float = 0.15,
    ) -> None:

        self._penalty = diversity_penalty

    # =====================================================
    # PUBLIC
    # =====================================================

    def rerank(
        self,
        results: list[HybridRetrievalResult],
    ) -> list[HybridRetrievalResult]:

        if not results:
            return results

        # -------------------------------------------------
        # INITIAL SORT
        # -------------------------------------------------

        ranked = sorted(
            results,
            key=lambda result: (result.fused_score),
            reverse=True,
        )

        # -------------------------------------------------
        # CATEGORY TRACKING
        # -------------------------------------------------

        category_counts = defaultdict(int)

        reranked = []

        # -------------------------------------------------
        # DIVERSITY-AWARE SCORING
        # -------------------------------------------------

        for result in ranked:

            dominant_category = self._extract_primary_category(result)

            penalty_multiplier = category_counts[dominant_category]

            diversity_penalty = penalty_multiplier * self._penalty

            adjusted_score = result.fused_score - diversity_penalty

            adjusted = result.model_copy(
                update={
                    "fused_score": round(
                        adjusted_score,
                        4,
                    )
                }
            )

            reranked.append(adjusted)

            category_counts[dominant_category] += 1

        # -------------------------------------------------
        # FINAL SORT
        # -------------------------------------------------

        reranked.sort(
            key=lambda result: (result.fused_score),
            reverse=True,
        )

        return reranked

    # =====================================================
    # INTERNALS
    # =====================================================

    def _extract_primary_category(
        self,
        result: HybridRetrievalResult,
    ) -> str:

        categories = result.symbolic_result.matched_categories

        if categories:
            return categories[0]

        
        return "unknown"

