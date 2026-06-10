# infrastructure/llm/metrics/llm_operation_context.py

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_DEFAULT_OPERATION = "unknown"

_llm_operation: ContextVar[str] = ContextVar("llm_operation", default=_DEFAULT_OPERATION)
_llm_attempt: ContextVar[int] = ContextVar("llm_attempt", default=0)


class LLMOperationContext:

    @classmethod
    def set_operation(cls, operation: str) -> Token:
        return _llm_operation.set(operation)

    @classmethod
    def get_operation(cls) -> str:
        return _llm_operation.get()

    @classmethod
    def reset(cls, token: Token) -> None:
        _llm_operation.reset(token)

    @classmethod
    def reset_attempt(cls) -> None:
        _llm_attempt.set(0)

    @classmethod
    def next_attempt(cls) -> int:
        attempt = _llm_attempt.get() + 1
        _llm_attempt.set(attempt)
        return attempt

    @classmethod
    @contextmanager
    def scope(cls, operation: str) -> Iterator[None]:
        token = cls.set_operation(operation)
        cls.reset_attempt()
        try:
            yield
        finally:
            cls.reset(token)
            cls.reset_attempt()
