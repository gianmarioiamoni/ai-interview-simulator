# tests/services/interview_reasoner/profile/conftest.py
"""Shared fixtures for profile engine tests (M2-6C)."""

import uuid

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from tests.domain.profile.profile_test_helpers import (
    candidate_profile_with_dimension_scores,
)


def uid() -> str:
    return str(uuid.uuid4())


def mk_sig(
    q: int = 1,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
    stype: EvidenceType = EvidenceType.KNOWLEDGE_GAP,
    source: EvidenceSource = EvidenceSource.EVALUATION,
    strength: float = 0.7,
    area: str = "api",
) -> EvidenceSignal:
    return EvidenceSignal(
        id=uid(), question_index=q, question_area=area,
        dimension=dim, polarity=polarity, signal_type=stype,
        strength=strength, source=source, timestamp_question_index=q,
    )


def mk_trace(
    avg: float = 50.0,
    last: float = 50.0,
    ev: int = 3,
    trend: Trend = Trend.STABLE,
    conf: float = 0.3,
    last_q: int = 1,
) -> DimensionTrace:
    return DimensionTrace(
        average_score=avg, last_score=last,
        trend=trend, confidence=conf,
        evidence_count=ev, last_updated_question=last_q,
    )


def empty_profile() -> CandidateProfile:
    return CandidateProfile()


def profile_with_trace(
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    **trace_kwargs,
) -> CandidateProfile:
    return candidate_profile_with_dimension_scores({dim: mk_trace(**trace_kwargs)})
