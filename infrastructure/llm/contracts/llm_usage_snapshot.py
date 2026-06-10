# infrastructure/llm/contracts/llm_usage_snapshot.py

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class LLMUsageSnapshot:
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    cache_read_tokens: Optional[int]
    reasoning_tokens: Optional[int]
    model_name: Optional[str]
    finish_reason: Optional[str]
    request_id: Optional[str]
    source: str
