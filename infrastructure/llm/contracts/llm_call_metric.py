# infrastructure/llm/contracts/llm_call_metric.py

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
