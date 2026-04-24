from app.ui.dto.dimension_score_dto import DimensionScoreDTO


class DimensionScoreMapper:

    @staticmethod
    def map(final_evaluation):

        if not final_evaluation.dimension_scores:
            return []

        return [
            DimensionScoreDTO(dimension=dim, score=score)
            for dim, score in final_evaluation.dimension_scores.items()
        ]
