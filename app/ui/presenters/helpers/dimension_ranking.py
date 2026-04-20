# app/ui/presenters/helpers/dimension_ranking.py

from typing import List, Optional

from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionRanking:

    @staticmethod
    def compute(
        dimensions: List[DimensionScoreDTO],
    ) -> tuple[Optional[DimensionScoreDTO], Optional[DimensionScoreDTO]]:

        evaluated = [d for d in dimensions if d.score is not None]

        if not evaluated:
            return None, None

        strongest = max(evaluated, key=lambda x: x.score)
        weakest = min(evaluated, key=lambda x: x.score)

        return strongest, weakest
