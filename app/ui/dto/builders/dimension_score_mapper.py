# app/ui/dto/builders/dimension_score_mapper.py

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from typing import List, Dict


class DimensionScoreMapper:

    def map(
        self,
        dimension_scores: Dict,
        weighted_breakdown: Dict | None = None,
    ) -> List[DimensionScoreDTO]:

        if not dimension_scores:
            return []

        results = []

        for dim, score in dimension_scores.items():

            # -----------------------------------------
            # NORMALIZE KEY
            # -----------------------------------------

            if hasattr(dim, "value"):
                dim_key = dim.value
            else:
                dim_key = str(dim)

            label = dim_key.replace("_", " ").title()

            # -----------------------------------------
            # WEIGHT / CONTRIBUTION
            # -----------------------------------------

            contribution = 0.0
            weight = 0.0

            if weighted_breakdown and dim in weighted_breakdown:
                contribution = weighted_breakdown.get(dim, 0.0)

                if score > 0:
                    weight = round(contribution / score, 2)

            # -----------------------------------------
            # STATUS
            # -----------------------------------------

            if score >= 85:
                status = "strong"
            elif score >= 70:
                status = "moderate"
            else:
                status = "weak"

            results.append(
                DimensionScoreDTO(
                    name=label,
                    score=score,
                    max_score=100.0,
                    weight=weight,
                    contribution=contribution,
                    is_evaluated=True,
                    status=status,
                )
            )

        return results
