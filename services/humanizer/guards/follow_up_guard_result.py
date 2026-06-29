# services/humanizer/guards/follow_up_guard_result.py

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FollowUpGuardResult:
    """Immutable result returned by FollowUpGuard.validate()."""

    accepted: bool
    score: float                        # [0.0, 1.0] — fraction of rules passed
    reasons: tuple[str, ...]            # human-readable rejection reasons
    warnings: tuple[str, ...]           # non-blocking observations
    failed_rules: tuple[str, ...]       # rule identifiers that failed

    @staticmethod
    def build(
        *,
        failed: list[str],
        warnings: list[str],
        total_rules: int,
    ) -> "FollowUpGuardResult":
        passed = total_rules - len(failed)
        score = passed / total_rules if total_rules > 0 else 0.0
        return FollowUpGuardResult(
            accepted=len(failed) == 0,
            score=round(score, 4),
            reasons=tuple(failed),
            warnings=tuple(warnings),
            failed_rules=tuple(failed),
        )
