# domain/contracts/interview/interview_cost_metrics.py

from dataclasses import dataclass, field


@dataclass(slots=True)
class OperationCostMetrics:
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(slots=True)
class InterviewCostMetrics:
    total_cost_usd: float
    cost_per_question_usd: float
    operations: list[OperationCostMetrics] = field(default_factory=list)
