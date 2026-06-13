# services/interview_evaluation/steps/weight_normalization_step.py

from typing import Dict, Tuple

from domain.contracts.user.role import RoleType, ROLE_WEIGHTS

from app.core.logger import get_logger

logger = get_logger(__name__)


class WeightNormalizationStep:
    """
    Filters role weights to match available dimension scores, normalises
    them, computes a weighted breakdown and re-derives the overall score.

    Responsibilities:
    - Filter ROLE_WEIGHTS to present dimensions only
    - Normalise weights to sum to 1.0
    - Compute per-dimension weighted contribution
    - Derive the final overall score
    """

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def compute(
        self,
        dimension_scores: Dict,
        role: RoleType,
    ) -> Tuple[Dict, float]:
        """
        Return (weighted_breakdown, overall_score).

        Raises ValueError if total weight is zero after filtering.
        """

        weights = ROLE_WEIGHTS[role]

        valid_weights = {
            dim: weight
            for dim, weight in weights.items()
            if dim in dimension_scores
        }

        total_weight = sum(valid_weights.values())

        if total_weight == 0:
            raise ValueError("Total weight is zero after filtering dimensions")

        normalized_weights = {
            dim: weight / total_weight for dim, weight in valid_weights.items()
        }

        weighted_breakdown: Dict = {}

        for dim, score in dimension_scores.items():

            if dim not in normalized_weights:
                continue

            weight = normalized_weights[dim]
            weighted_breakdown[dim] = round(score * weight, 2)

        overall_score = round(sum(weighted_breakdown.values()), 1)

        return weighted_breakdown, overall_score
