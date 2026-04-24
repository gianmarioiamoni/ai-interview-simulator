# app/ui/dto/builders/dimension_score_mapper.py

from typing import List, Dict, Any

from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionScoreMapper:
    # Maps dimension_scores dict to DimensionScoreDTO list

    def map(self, dimension_scores: Dict[Any, float] | None) -> List[DimensionScoreDTO]:

        if not dimension_scores:
            return []

        results: List[DimensionScoreDTO] = []

        for dim, score in dimension_scores.items():

            # -----------------------------------------------------
            # HANDLE ENUM OR STRING
            # -----------------------------------------------------

            if hasattr(dim, "value"):
                dim_value = dim.value
            else:
                dim_value = str(dim)

            # -----------------------------------------------------
            # HUMAN READABLE LABEL
            # -----------------------------------------------------

            label = dim_value.replace("_", " ").title()

            results.append(DimensionScoreDTO(name=label, score=score))

        return results
