# domain/contracts/interview/interview_metrics.py

from dataclasses import dataclass, field


@dataclass(slots=True)
class OperationMetrics:
    operation: str
    calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    avg_latency_ms: float


@dataclass(slots=True)
class InterviewMetrics:
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_retries: int
    avg_latency_ms: float
    operations: list[OperationMetrics] = field(default_factory=list)
