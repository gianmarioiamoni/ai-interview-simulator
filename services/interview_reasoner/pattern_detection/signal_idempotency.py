# services/interview_reasoner/pattern_detection/signal_idempotency.py
"""Detector-level idempotency guard (M2-6A, P1).

Each PatternDetector is responsible for NOT re-emitting a signal that is
structurally equivalent to one already present in the EvidenceStore.

Identity key: (signal_type, dimension, question_index, source)

This module provides a pure helper that detectors use to filter their
candidate output list before returning.  EvidenceStore remains a passive,
immutable repository with no deduplication logic of its own.
"""

from __future__ import annotations

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_store import EvidenceStore


def _identity_key(sig: EvidenceSignal) -> tuple:
    return (sig.signal_type, sig.dimension, sig.question_index, sig.source)


def filter_new_signals(
    candidates: list[EvidenceSignal],
    store: EvidenceStore,
) -> list[EvidenceSignal]:
    """Return only signals whose identity key is absent from `store`.

    O(n + m) where n = len(store.signals), m = len(candidates).
    Pure function; no side effects.
    """
    existing_keys = {_identity_key(s) for s in store.signals}
    return [s for s in candidates if _identity_key(s) not in existing_keys]
