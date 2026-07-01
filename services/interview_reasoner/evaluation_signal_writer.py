# services/interview_reasoner/evaluation_signal_writer.py
"""EvaluationSignalWriter — production writer for EVALUATION-source EvidenceSignals.

This is the missing bridge identified in M2-7M audit (P0-1).

Responsibility:
  Convert QuestionEvaluation scoring results into EvidenceSignals with
  source=EvidenceSource.EVALUATION so that EvaluationSignalDetector can
  read and bridge them into the pattern detection pipeline (ADR-052).

Contract:
  - Called by reasoner_node BEFORE ReasonerService.reason().
  - Idempotent: never writes a signal for a question_index already present
    in the store with source=EVALUATION.
  - Deterministic: no LLM, no randomness.
  - O(n) in store size.
  - Single writer for EVALUATION-source signals (ADR-038, ADR-052).
"""

from __future__ import annotations

import uuid

from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

# Score thresholds for KNOWLEDGE_GAP / SHALLOW_ANSWER / REASONING_GAP classification.
_STRONG_PASS_THRESHOLD = 80.0   # score >= 80: no negative signals
_PARTIAL_PASS_THRESHOLD = 50.0  # 50 <= score < 80: SHALLOW_ANSWER
_FAIL_THRESHOLD = 30.0          # score < 50: KNOWLEDGE_GAP
# score < 30: REASONING_GAP (severe failure)


def write_evaluation_signals(
    evaluation: QuestionEvaluation,
    question_index: int,
    question_area: str,
    store: EvidenceStore,
) -> EvidenceStore:
    """Append EVALUATION-source signals for `evaluation` to `store`.

    Idempotent: if signals for `question_index` with source=EVALUATION already
    exist in the store, no new signals are written.

    Returns the (possibly new) EvidenceStore. Never mutates `store`.
    """
    # Idempotency guard: skip if already written for this question.
    already_written = any(
        sig.source == EvidenceSource.EVALUATION and sig.question_index == question_index
        for sig in store.signals
    )
    if already_written:
        return store

    signals = _build_signals(evaluation, question_index, question_area)
    for sig in signals:
        try:
            store = store.append(sig)
        except ValueError:
            # EvidenceStore capacity reached — stop silently (ADR-046).
            break
    return store


def _build_signals(
    evaluation: QuestionEvaluation,
    question_index: int,
    question_area: str,
) -> list[EvidenceSignal]:
    """Derive EvidenceSignals from a QuestionEvaluation score.

    Maps score bands to the BRIDGEABLE_TYPES consumed by EvaluationSignalDetector:
      KNOWLEDGE_GAP    — severe failure (score < 30)
      REASONING_GAP    — significant failure (30 <= score < 50)
      SHALLOW_ANSWER   — partial answer (50 <= score < 80)
      (no negative signal) — strong pass (score >= 80)
    """
    score = evaluation.score
    area = question_area or "unknown"

    if score >= _STRONG_PASS_THRESHOLD:
        return []

    if score < _FAIL_THRESHOLD:
        etype = EvidenceType.KNOWLEDGE_GAP
        strength = round(1.0 - (score / _FAIL_THRESHOLD), 4)
    elif score < _PARTIAL_PASS_THRESHOLD:
        etype = EvidenceType.REASONING_GAP
        strength = round(1.0 - (score / _PARTIAL_PASS_THRESHOLD), 4)
    else:
        etype = EvidenceType.SHALLOW_ANSWER
        strength = round(1.0 - (score / _STRONG_PASS_THRESHOLD), 4)

    return [
        EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=question_index,
            question_area=area,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=etype,
            strength=min(1.0, max(0.0, strength)),
            source=EvidenceSource.EVALUATION,
            timestamp_question_index=question_index,
        )
    ]
