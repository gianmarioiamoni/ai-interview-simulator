from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionScoreMapper:

    @staticmethod
    def map(final_evaluation):

        if not final_evaluation.dimension_scores:
            return []

        return [
            DimensionScoreDTO(name=dim.value.replace("_", " ").title(), score=score)
            for dim, score in final_evaluation.dimension_scores.items()
        ]
