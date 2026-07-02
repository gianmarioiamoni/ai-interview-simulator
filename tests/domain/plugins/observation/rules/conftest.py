# tests/domain/plugins/observation/rules/conftest.py

import uuid
import pytest

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension


def make_signal(
    *,
    dimension: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    polarity: EvidencePolarity = EvidencePolarity.POSITIVE,
    signal_type: EvidenceType = EvidenceType.DEMONSTRATED_DEPTH,
    strength: float = 0.8,
    question_index: int = 0,
    question_area: str = "algorithms",
    source: EvidenceSource = EvidenceSource.EVALUATION,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=question_index,
        question_area=question_area,
        dimension=dimension,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=source,
        timestamp_question_index=question_index,
    )


def make_context(
    signals: list[EvidenceSignal],
    question_index: int = 0,
    session_id: str = "session-test-001",
) -> ObservationExtractionContext:
    return ObservationExtractionContext(
        signals=tuple(signals),
        question_index=question_index,
        session_id=session_id,
    )


@pytest.fixture
def session_id() -> str:
    return "session-test-001"


@pytest.fixture
def positive_tech_signal():
    return make_signal(
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.POSITIVE,
        strength=0.8,
    )


@pytest.fixture
def negative_tech_signal():
    return make_signal(
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        strength=0.2,
    )


@pytest.fixture
def positive_problem_signal():
    return make_signal(
        dimension=ProfileDimension.PROBLEM_SOLVING,
        polarity=EvidencePolarity.POSITIVE,
        signal_type=EvidenceType.REASONING_DEPTH_HIGH,
        strength=0.75,
    )


@pytest.fixture
def negative_problem_signal():
    return make_signal(
        dimension=ProfileDimension.PROBLEM_SOLVING,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.REASONING_DEPTH_LOW,
        strength=0.4,
    )
