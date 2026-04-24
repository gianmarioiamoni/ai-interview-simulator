# app/ui/dto/builders/dimension_score_mapper.py

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from typing import List


class DimensionScoreMapper:
    # Maps a QuestionEvaluation object to a list of DimensionScoreDTO objects.

    def map(
        self,
        evaluation: InterviewEvaluation | None
    ) -> List[DimensionScoreDTO]:

        if not evaluation or not evaluation.dimension_scores:
            return []

        results = []

        for dim, score in evaluation.dimension_scores.items():

            # -----------------------------------------------------
            # HANDLE ENUM OR STRING
            # -----------------------------------------------------

            if hasattr(dim, "value"):
                dim_value = dim.value
            else:
                dim_value = str(dim)

            # -----------------------------------------------------
            # HUMAN READABLE
            # -----------------------------------------------------

            label = dim_value.replace("_", " ").title()

            results.append(DimensionScoreDTO(name=label, score=score))

        return results
