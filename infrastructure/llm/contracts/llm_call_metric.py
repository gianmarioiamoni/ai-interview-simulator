# infrastructure/llm/contracts/llm_call_metric.py
#
# EPIC-08 P3/C7 — existing ObservingLLMAdapter metric surface.
# Freeze/EPIC-09 aliases expose AR-07 fields without a second ownership path.

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class LLMCallMetric:
    operation: str
    model_name: Optional[str]
    latency_ms: float
    attempt: int
    success: bool
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    timestamp: datetime
    error_type: Optional[str] = None

    @property
    def model(self) -> Optional[str]:
        """Freeze §6.1 / EPIC-09 alias for model_name."""
        return self.model_name

    @property
    def prompt_tokens(self) -> Optional[int]:
        """Freeze §6.1 alias for input_tokens."""
        return self.input_tokens

    @property
    def completion_tokens(self) -> Optional[int]:
        """Freeze §6.1 alias for output_tokens."""
        return self.output_tokens

    @property
    def duration_ms(self) -> float:
        """Freeze §6.1 / EPIC-09 alias for latency_ms."""
        return self.latency_ms

    @property
    def status(self) -> str:
        """Request outcome for observability consumers."""
        return "success" if self.success else "failure"

    def as_ar07_fields(self) -> dict[str, object]:
        """
        AR-07 fields available on the existing collector path.

        Used by C8 structured-log bridge; does not emit logs itself (OBS-04).
        """
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_type": self.error_type,
            "operation": self.operation,
            "attempt": self.attempt,
        }
