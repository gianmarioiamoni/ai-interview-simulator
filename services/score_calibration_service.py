# services/score_calibration_service.py

from domain.contracts.question.question_evaluation import QuestionEvaluation


class ScoreCalibrationService:

    def calibrate(self, evaluation: QuestionEvaluation) -> QuestionEvaluation:

        raw_score = evaluation.score

        calibrated = self._apply_curve(raw_score)

        return evaluation.model_copy(
            update={
                "score": calibrated,
            }
        )

    # ---------------------------------------------------------

    def _apply_curve(self, score: float) -> float:

        # -----------------------------------------------------
        # LLM bias correction curve
        # -----------------------------------------------------

        if score >= 90:
            score -= 8

        elif score >= 80:
            score -= 10

        elif score >= 70:
            score -= 8

        elif score >= 60:
            score -= 5

        else:
            score -= 2

        # clamp
        score = max(0.0, min(100.0, score))

        return round(score, 1)
