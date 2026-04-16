# app/ui/dto/builders/dimension_mapper.py

from typing import List

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class DimensionMapper:

    def map(self, final_evaluation) -> List[DimensionScoreDTO]:

        dimension_scores = []

        for dim in final_evaluation.performance_dimensions:

            score = dim.score if dim.score is not None else 0.0
            is_evaluated = dim.score is not None

            dim_type = next(
                (k for k, v in DIMENSION_LABELS.items() if v == dim.name),
                None,
            )

            contribution = 0.0
            weight = 0.0

            if dim_type and dim_type in final_evaluation.weighted_breakdown:
                contribution = final_evaluation.weighted_breakdown[dim_type]

                if score > 0:
                    weight = round(contribution / score, 2)

            dimension_scores.append(
                DimensionScoreDTO(
                    name=dim.name,
                    score=score,
                    max_score=100,
                    weight=weight,
                    contribution=contribution,
                    is_evaluated=is_evaluated,
                )
            )

        return dimension_scores
