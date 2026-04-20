# app/ui/dto/builders/dimension_mapper.py

from typing import List

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class DimensionMapper:

    def map(self, final_evaluation) -> List[DimensionScoreDTO]:

        raw_dimensions = []

        # ---------------------------------------------------------
        # Extract raw data first (no DTO yet)
        # ---------------------------------------------------------

        for dim in final_evaluation.performance_dimensions:

            score = dim.score if dim.score is not None else None
            is_evaluated = score is not None

            dim_type = next(
                (k for k, v in DIMENSION_LABELS.items() if v == dim.name),
                None,
            )

            contribution = 0.0
            weight = 0.0

            if dim_type and dim_type in final_evaluation.weighted_breakdown:
                contribution = final_evaluation.weighted_breakdown[dim_type]

                if score and score > 0:
                    weight = round(contribution / score, 2)

            raw_dimensions.append(
                {
                    "name": dim.name,
                    "score": score,
                    "weight": weight,
                    "contribution": contribution,
                    "is_evaluated": is_evaluated,
                }
            )

        # ---------------------------------------------------------
        # Ranking (only evaluated)
        # ---------------------------------------------------------

        evaluated = [d for d in raw_dimensions if d["score"] is not None]

        if evaluated:
            sorted_dims = sorted(
                evaluated,
                key=lambda x: x["score"],
                reverse=True,
            )

            strongest_name = sorted_dims[0]["name"]
            weakest_name = sorted_dims[-1]["name"]
        else:
            strongest_name = None
            weakest_name = None

        # ---------------------------------------------------------
        # Classification logic (relative + absolute)
        # ---------------------------------------------------------

        def classify(score: float, is_weakest: bool) -> str:

            if score is None:
                return "⚪ Not Evaluated"

            if is_weakest:
                if score < 70:
                    return "🔴 Weak"
                elif score < 80:
                    return "🟡 Needs Improvement"
                else:
                    return "🟡 Relative Weakness"

            if score >= 85:
                return "🟢 Strong"
            elif score >= 70:
                return "🟡 Average"
            else:
                return "🔴 Weak"

        # ---------------------------------------------------------
        # Build DTOs with status
        # ---------------------------------------------------------

        dimension_scores = []

        for d in raw_dimensions:

            status = classify(
                d["score"],
                is_weakest=(d["name"] == weakest_name),
            )

            dimension_scores.append(
                DimensionScoreDTO(
                    name=d["name"],
                    score=d["score"] if d["score"] is not None else 0.0,
                    max_score=100,
                    weight=d["weight"],
                    contribution=d["contribution"],
                    is_evaluated=d["is_evaluated"],
                    status=status,  # 🔥 NEW
                )
            )

        return dimension_scores
