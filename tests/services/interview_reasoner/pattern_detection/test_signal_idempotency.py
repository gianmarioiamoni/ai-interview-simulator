# tests/services/interview_reasoner/pattern_detection/test_signal_idempotency.py
"""Tests for signal_idempotency helper (M2-6A, P1)."""

import uuid
import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals


def _sig(
    q: int = 0,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    stype: EvidenceType = EvidenceType.SHALLOW_ANSWER,
    source: EvidenceSource = EvidenceSource.PATTERN_DETECTOR,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()), question_index=q, question_area="a",
        dimension=dim, polarity=EvidencePolarity.NEGATIVE,
        signal_type=stype, strength=0.5, source=source,
        timestamp_question_index=q,
    )


def test_empty_store_all_candidates_pass():
    store = EvidenceStore()
    candidates = [_sig(0), _sig(1)]
    assert len(filter_new_signals(candidates, store)) == 2


def test_identical_key_filtered():
    s = _sig(0)
    store = EvidenceStore(signals=[s])
    duplicate = _sig(0)  # same key: (stype, dim, q, source)
    result = filter_new_signals([duplicate], store)
    assert result == []


def test_different_question_not_filtered():
    s = _sig(0)
    store = EvidenceStore(signals=[s])
    new_sig = _sig(1)  # different question_index → different key
    result = filter_new_signals([new_sig], store)
    assert len(result) == 1


def test_different_source_not_filtered():
    s = _sig(0, source=EvidenceSource.EVALUATION)
    store = EvidenceStore(signals=[s])
    new_sig = _sig(0, source=EvidenceSource.PATTERN_DETECTOR)
    result = filter_new_signals([new_sig], store)
    assert len(result) == 1


def test_different_dim_not_filtered():
    s = _sig(0, dim=ProfileDimension.TECHNICAL_DEPTH)
    store = EvidenceStore(signals=[s])
    new_sig = _sig(0, dim=ProfileDimension.COMMUNICATION)
    result = filter_new_signals([new_sig], store)
    assert len(result) == 1


def test_different_type_not_filtered():
    s = _sig(0, stype=EvidenceType.SHALLOW_ANSWER)
    store = EvidenceStore(signals=[s])
    new_sig = _sig(0, stype=EvidenceType.KNOWLEDGE_GAP)
    result = filter_new_signals([new_sig], store)
    assert len(result) == 1


def test_empty_candidates():
    store = EvidenceStore(signals=[_sig(0)])
    assert filter_new_signals([], store) == []


def test_multiple_candidates_partial_filter():
    existing = _sig(0)
    store = EvidenceStore(signals=[existing])
    dup = _sig(0)
    new_one = _sig(1)
    result = filter_new_signals([dup, new_one], store)
    assert len(result) == 1
    assert result[0].question_index == 1


def test_pure_function_does_not_mutate_store():
    s = _sig(0)
    store = EvidenceStore(signals=[s])
    filter_new_signals([_sig(1)], store)
    assert len(store.signals) == 1
