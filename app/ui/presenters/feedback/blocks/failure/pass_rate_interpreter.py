# app/ui/presenters/feedback/blocks/failure/pass_rate_interpreter.py

from infrastructure.config.evaluation import (
    FAILURE_PASS_RATE_MINOR,
    FAILURE_PASS_RATE_PARTIAL,
)


class PassRateInterpreter:
    """Maps a pass-rate float to a human-readable severity message. Stateless."""

    def interpret(self, pass_rate: float) -> str:
        if pass_rate >= FAILURE_PASS_RATE_MINOR:
            return "Minor issues detected."
        if pass_rate >= FAILURE_PASS_RATE_PARTIAL:
            return "Partial correctness — several cases failing."
        return "Fundamental issues in solution."
