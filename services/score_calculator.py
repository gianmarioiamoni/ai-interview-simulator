# services/score_calculator.py

from domain.contracts.feedback.quality import Quality
from infrastructure.config.evaluation import (
    CODING_QUALITY_CORRECT_THRESHOLD,
    CODING_QUALITY_PARTIAL_THRESHOLD,
    EXECUTION_SLOW_MS,
    EXECUTION_FAST_MS,
    EXECUTION_SLOW_PENALTY,
    EXECUTION_FAST_BONUS,
)


def compute_quality(
    *,
    passed: int | None,
    total: int | None,
    execution_time_ms: float | None = None,
) -> tuple[float, Quality]:
    """Canonical quality computation. Single source of truth for coding/DB quality."""

    if total is None or total == 0:
        return 0.0, Quality.INCORRECT

    passed = passed or 0

    correctness_ratio = passed / total
    score = correctness_ratio * 100

    is_inefficient = False

    if execution_time_ms is not None:
        if execution_time_ms > EXECUTION_SLOW_MS:
            is_inefficient = True
            score -= EXECUTION_SLOW_PENALTY
        elif execution_time_ms < EXECUTION_FAST_MS:
            score += EXECUTION_FAST_BONUS

    score = max(0, min(100, score))

    if score == 100:
        quality = Quality.OPTIMAL if not is_inefficient else Quality.INEFFICIENT
    elif score >= CODING_QUALITY_CORRECT_THRESHOLD:
        quality = Quality.CORRECT
    elif score >= CODING_QUALITY_PARTIAL_THRESHOLD:
        quality = Quality.PARTIAL
    else:
        quality = Quality.INCORRECT

    return round(score, 2), quality


class ScoreCalculator:

    def compute(
        self,
        *,
        passed: int | None,
        total: int | None,
        execution_time_ms: float | None = None,
    ) -> tuple[float, Quality]:
        return compute_quality(
            passed=passed,
            total=total,
            execution_time_ms=execution_time_ms,
        )
