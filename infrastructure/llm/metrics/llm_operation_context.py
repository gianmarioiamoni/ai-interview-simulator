# infrastructure/llm/metrics/llm_operation_context.py

from contextvars import ContextVar

_llm_operation: ContextVar[str] = ContextVar("llm_operation", default="unknown")
_llm_attempt: ContextVar[int] = ContextVar("llm_attempt", default=0)


def get_operation() -> str:
    return _llm_operation.get()


def set_operation(operation: str) -> None:
    _llm_operation.set(operation)


def reset_attempt() -> None:
    _llm_attempt.set(0)


def next_attempt() -> int:
    attempt = _llm_attempt.get() + 1
    _llm_attempt.set(attempt)
    return attempt
