# infrastructure/execution/execution_lifecycle.py

import time
from enum import Enum
from typing import Optional

from infrastructure.execution.contracts.execution_result import ExecutionResult


class ExecutionPhase(str, Enum):
    PRE_VALIDATION = "pre_validation"
    DISPATCH = "dispatch"
    POST_PROCESSING = "post_processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ExecutionLifecycle:
    """Manages execution phases and records transitions with timestamps."""

    def __init__(self) -> None:
        self._current_phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION
        self._start_time: float = time.monotonic()
        self._transitions: list[tuple[ExecutionPhase, float]] = []
        self._result: Optional[ExecutionResult] = None
        self._error: Optional[str] = None
        self._is_complete: bool = False

    @property
    def current_phase(self) -> ExecutionPhase:
        return self._current_phase

    @property
    def elapsed_ms(self) -> float:
        return (time.monotonic() - self._start_time) * 1000.0

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @property
    def transitions(self) -> list[tuple[ExecutionPhase, float]]:
        return list(self._transitions)

    def start(self) -> None:
        self._start_time = time.monotonic()
        self._transitions = [(self._current_phase, self._start_time)]

    def transition(self, phase: ExecutionPhase) -> None:
        self._current_phase = phase
        self._transitions.append((phase, time.monotonic()))

    def complete(self, result: ExecutionResult) -> None:
        self._result = result
        self._is_complete = True
        self.transition(ExecutionPhase.COMPLETE)

    def fail(self, error: str) -> None:
        self._error = error
        self._is_complete = True
        self.transition(ExecutionPhase.FAILED)
