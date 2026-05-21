# services/interview_orchestration/interview_semantic_spread_scorer.py

from pydantic import BaseModel


class SemanticSpreadScore(BaseModel):

    average_similarity: float

    spread_score: float

    classification: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class InterviewSemanticSpreadScorer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        average_similarity: float,
    ) -> SemanticSpreadScore:

        spread_score = self._calculate_spread_score(average_similarity)

        classification = self._classify(average_similarity)

        return SemanticSpreadScore(
            average_similarity=(
                round(
                    average_similarity,
                    4,
                )
            ),
            spread_score=(spread_score),
            classification=(classification),
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _calculate_spread_score(
        self,
        similarity: float,
    ) -> float:

        spread = 1.0 - similarity

        return round(
            max(
                0.0,
                min(spread, 1.0),
            ),
            4,
        )

    def _classify(
        self,
        similarity: float,
    ) -> str:

        if similarity >= 0.75:
            return "redundant"

        if similarity >= 0.55:
            return "clustered"

        if similarity >= 0.30:
            return "healthy"

        return "highly_diverse"
