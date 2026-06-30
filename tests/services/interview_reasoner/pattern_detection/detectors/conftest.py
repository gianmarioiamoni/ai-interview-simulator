# tests/services/interview_reasoner/pattern_detection/detectors/conftest.py
"""Shared fixtures for pattern detector tests."""

import uuid
import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.coverage_state import CoverageState
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from domain.contracts.reasoning.trend import Trend


def _uid() -> str:
    return str(uuid.uuid4())


def make_signal(
    q_idx: int = 0,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
    signal_type: EvidenceType = EvidenceType.SHALLOW_ANSWER,
    strength: float = 0.7,
    area: str = "area",
) -> EvidenceSignal:
    return EvidenceSignal(
        id=_uid(),
        question_index=q_idx,
        question_area=area,
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


def make_input(
    question_index: int = 3,
    area: str = "databases",
    memory: InterviewMemory | None = None,
) -> ReasonerInput:
    return ReasonerInput(
        session_id="test-session",
        question_index=question_index,
        interview_memory=memory or InterviewMemory(),
        current_question_area=area,
    )


def make_dim_trace(
    trend: Trend = Trend.STABLE,
    average_score: float = 60.0,
    last_score: float | None = 60.0,
    evidence_count: int = 3,
    confidence: float = 0.6,
) -> DimensionTrace:
    return DimensionTrace(
        trend=trend,
        average_score=average_score,
        last_score=last_score,
        evidence_count=evidence_count,
        confidence=confidence,
    )


def make_reasoning_entry(
    q_idx: int = 0,
    dominant_dimension: ProfileDimension | None = ProfileDimension.TECHNICAL_DEPTH,
    reasoning_confidence: float = 0.7,
) -> ReasoningEntry:
    return ReasoningEntry(
        question_index=q_idx,
        dominant_dimension=dominant_dimension,
        reasoning_confidence=reasoning_confidence,
    )
