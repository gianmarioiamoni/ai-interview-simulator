# services/score_calculator.py

from domain.contracts.quality import Quality


class ScoreCalculator:

    def compute(
        self,
        *,
        passed: int | None,
        total: int | None,
        execution_time_ms: float | None = None,
    ) -> tuple[float, Quality]:

        # -----------------------------------------------------
        # SAFETY
        # -----------------------------------------------------

        if total is None or total == 0:
            return 0.0, Quality.INCORRECT

        passed = passed or 0

        # -----------------------------------------------------
        # BASE SCORE (correctness)
        # -----------------------------------------------------

        correctness_ratio = passed / total
        score = correctness_ratio * 100

        # -----------------------------------------------------
        # PERFORMANCE ADJUSTMENT
        # -----------------------------------------------------

        is_inefficient = False

        if execution_time_ms is not None:

            if execution_time_ms > 300:
                is_inefficient = True
                score -= 5

            elif execution_time_ms < 50:
                score += 2

        # clamp
        score = max(0, min(100, score))

        # -----------------------------------------------------
        # QUALITY MAPPING
        # -----------------------------------------------------

        if score == 100:
            quality = Quality.OPTIMAL if not is_inefficient else Quality.INEFFICIENT

        elif score >= 80:
            quality = Quality.CORRECT

        elif score >= 50:
            quality = Quality.PARTIAL

        else:
            quality = Quality.INCORRECT

        return round(score, 2), quality
