# tests/performance/helpers.py
# EPIC-V13-09 C1 — shared SLO measurement helpers (harness-only; MEAS-01/07).

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def measure_wall_clock_ms(operation: Callable[[], T]) -> tuple[T, float]:
    """Run *operation* and return ``(result, elapsed_ms)`` via ``perf_counter``."""
    started = time.perf_counter()
    result = operation()
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return result, elapsed_ms


def percentile_nearest_rank(samples_ms: list[float], percentile: float) -> float:
    """Nearest-rank percentile over a non-empty sample (inclusive upper bound)."""
    if not samples_ms:
        raise ValueError("samples_ms must be non-empty")
    if not 0.0 < percentile <= 100.0:
        raise ValueError("percentile must be in (0, 100]")

    ordered = sorted(samples_ms)
    rank = max(1, math.ceil((percentile / 100.0) * len(ordered)))
    return ordered[rank - 1]


def p99_ms(samples_ms: list[float]) -> float:
    """P99 latency in milliseconds (nearest-rank)."""
    return percentile_nearest_rank(samples_ms, 99.0)
