# infrastructure/llm/observability/observing_llm_adapter.py

import time
from datetime import datetime, timezone
from typing import Any, Type, TypeVar

from langchain_core.messages import AIMessage
from pydantic import BaseModel

from app.core.logger import get_logger
from app.ports.llm_port import LLMPort, LLMResponse
from infrastructure.config.settings import settings
from infrastructure.llm.contracts.llm_call_metric import LLMCallMetric
from infrastructure.llm.metrics.interview_metrics_collector import InterviewMetricsCollector
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.observability.token_usage_extractor import TokenUsageExtractor

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MODEL_FALLBACK = settings.chat_model


class _ObservingRawLLMProxy:

    def __init__(
        self,
        wrapped: Any,
        collector: InterviewMetricsCollector,
        model_fallback: str,
    ) -> None:
        self._wrapped = wrapped
        self._collector = collector
        self._model_fallback = model_fallback

    def invoke(self, messages: Any, *args: Any, **kwargs: Any) -> Any:
        operation = LLMOperationContext.get_operation()
        attempt = LLMOperationContext.next_attempt()
        started = time.monotonic()
        raw_message: AIMessage | None = None
        success = False
        error_type: str | None = None

        try:
            raw_message = self._wrapped.invoke(messages, *args, **kwargs)
            success = True
            return raw_message
        except Exception as exc:
            success = False
            error_type = type(exc).__name__
            raise
        finally:
            latency_ms = (time.monotonic() - started) * 1000.0
            snapshot = (
                TokenUsageExtractor.extract(raw_message, self._model_fallback)
                if raw_message is not None and isinstance(raw_message, AIMessage)
                else TokenUsageExtractor.empty(self._model_fallback)
            )
            metric = LLMCallMetric(
                operation=operation,
                model_name=snapshot.model_name or self._model_fallback,
                latency_ms=latency_ms,
                attempt=attempt,
                success=success,
                input_tokens=snapshot.input_tokens,
                output_tokens=snapshot.output_tokens,
                total_tokens=snapshot.total_tokens,
                timestamp=datetime.now(timezone.utc),
                error_type=error_type,
            )
            self._collector.record(metric)
            _emit_llm_call_log(metric)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


class ObservingLLMAdapter(LLMPort):

    def __init__(
        self,
        wrapped: LLMPort,
        collector: InterviewMetricsCollector,
    ) -> None:
        self._wrapped = wrapped
        self._collector = collector
        self._model_fallback = _resolve_model_fallback(wrapped)
        self._install_raw_proxy(wrapped)

    def invoke(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        LLMOperationContext.reset_attempt()

        if system_prompt is not None:
            return self._wrapped.invoke(prompt, system_prompt=system_prompt)

        return self._wrapped.invoke(prompt)

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        LLMOperationContext.reset_attempt()
        return self._wrapped.invoke_json(prompt, schema)

    def _install_raw_proxy(self, wrapped: LLMPort) -> None:
        inner = getattr(wrapped, "_llm", None)
        if inner is None or isinstance(inner, _ObservingRawLLMProxy):
            return

        wrapped._llm = _ObservingRawLLMProxy(
            inner,
            self._collector,
            self._model_fallback,
        )


def _resolve_model_fallback(wrapped: LLMPort) -> str:
    inner = getattr(wrapped, "_llm", None)
    if inner is not None:
        model_name = getattr(inner, "model_name", None)
        if model_name:
            return str(model_name)
    return _DEFAULT_MODEL_FALLBACK


def _emit_llm_call_log(metric: LLMCallMetric) -> None:
    # Informal path retained until C8 bridges AR-07 fields to emit_structured_log.
    logger.info(
        "llm.call operation=%s model=%s latency_ms=%.2f "
        "input_tokens=%s output_tokens=%s total_tokens=%s "
        "attempt=%s success=%s error_type=%s",
        metric.operation,
        metric.model_name,
        metric.latency_ms,
        metric.input_tokens,
        metric.output_tokens,
        metric.total_tokens,
        metric.attempt,
        metric.success,
        metric.error_type,
    )
