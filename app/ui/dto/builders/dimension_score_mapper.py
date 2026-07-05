# app/ui/dto/builders/dimension_score_mapper.py
# EPIC-V13-05 Phase 9 — DimensionScoreMapper accepts tuple[ScoringDimension, ...] (R-16).
# The three-parameter signature (dimension_scores, weighted_breakdown, performance_dimensions)
# is removed. Use map(scoring_dimensions) exclusively.

from typing import List

from domain.contracts.report.scoring_dimension import ScoringDimension
from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionScoreMapper:

    def map(self, scoring_dimensions: tuple[ScoringDimension, ...]) -> List[DimensionScoreDTO]:
        if not scoring_dimensions:
            return []

        results = []
        for dim in scoring_dimensions:
            label = dim.dimension_type.value.replace("_", " ").title()

            weight = 0.0
            if dim.score > 0:
                weight = round(dim.weighted_contribution / dim.score, 2)

            results.append(
                DimensionScoreDTO(
                    name=label,
                    score=dim.score,
                    max_score=100.0,
                    weight=weight,
                    contribution=dim.weighted_contribution,
                    is_evaluated=True,
                    status=dim.level,
                    justification=dim.justification,
                )
            )

        return results
