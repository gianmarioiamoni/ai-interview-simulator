# infrastructure/llm/observability/llm_structured_log_bridge.py
#
# EPIC-08 P3/C8 — sole bridge from ObservingLLMAdapter metrics to Freeze §6.1
# structured emission (OBS-01/04/05). Does not collect metrics.

from __future__ import annotations

from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.observability.structured_log import emit_structured_log

_COMPONENT = "llm"
_EVENT = "llm.call"


def emit_llm_call_structured_log(metric: LLMCallMetric) -> dict[str, object]:
    """
    Translate an existing LLMCallMetric into the frozen structured-log schema.

    Observational only: emission failures are absorbed by emit_structured_log
    (OBS-03). Does not alter LLM control flow or collector ownership (OBS-04).
    """
    level = "ERROR" if metric.status == "failure" else "INFO"
    return emit_structured_log(
        event=_EVENT,
        component=_COMPONENT,
        status=metric.status,
        level=level,
        duration_ms=metric.duration_ms,
        model=metric.model,
        prompt_tokens=metric.prompt_tokens,
        completion_tokens=metric.completion_tokens,
        total_tokens=metric.total_tokens,
        error_type=metric.error_type,
    )
