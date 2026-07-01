# tests/domain/contracts/reasoning/test_enums.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.trend import Trend
from domain.contracts.reasoning.data_sufficiency import DataSufficiency
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal


def test_trend_values():
    assert Trend.IMPROVING == "improving"
    assert Trend.STABLE == "stable"
    assert Trend.DECLINING == "declining"
    assert Trend.INSUFFICIENT_DATA == "insufficient_data"
    assert len(Trend) == 4


def test_data_sufficiency_values():
    assert DataSufficiency.INSUFFICIENT == "insufficient"
    assert DataSufficiency.TENTATIVE == "tentative"
    assert DataSufficiency.CONFIDENT == "confident"
    assert DataSufficiency.STRONG == "strong"
    assert len(DataSufficiency) == 4


def test_evidence_polarity_values():
    assert EvidencePolarity.POSITIVE == "positive"
    assert EvidencePolarity.NEGATIVE == "negative"
    assert len(EvidencePolarity) == 2


def test_evidence_source_contains_derived():
    assert EvidenceSource.DERIVED == "derived"
    assert EvidenceSource.EVALUATION == "evaluation"
    assert EvidenceSource.FEEDBACK == "feedback"
    assert EvidenceSource.PATTERN_DETECTOR == "pattern_detector"
    assert len(EvidenceSource) == 4


def test_evidence_type_positive_and_negative():
    positive = {
        EvidenceType.REPEATED_STRENGTH,
        EvidenceType.RECOVERED_WEAKNESS,
        EvidenceType.DEMONSTRATED_DEPTH,
        EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED,
    }
    negative = {
        EvidenceType.REPEATED_WEAKNESS,
        EvidenceType.KNOWLEDGE_GAP,
        EvidenceType.COMMUNICATION_GAP,
        EvidenceType.REASONING_GAP,
        EvidenceType.CONFIDENCE_DROP,
        EvidenceType.MISSING_EVIDENCE,
        EvidenceType.SHALLOW_ANSWER,
        EvidenceType.CONTRADICTORY_ANSWER,
    }
    assert len(positive) == 4
    assert len(negative) == 8
    assert len(EvidenceType) == 16  # 12 original + 4 reasoning-depth types (M2-7B)


def test_profile_dimension_five_values():
    assert ProfileDimension.ENGINEERING_JUDGMENT == "engineering_judgment"
    assert len(ProfileDimension) == 5
    assert "engineering_judgment" in [d.value for d in ProfileDimension]


def test_profile_dimension_no_trade_off_awareness():
    values = [d.value for d in ProfileDimension]
    assert "trade_off_awareness" not in values


def test_profile_signal_values():
    assert len(ProfileSignal) == 4
    assert ProfileSignal.CONFIDENCE == "confidence"
    assert ProfileSignal.CONSISTENCY == "consistency"
    assert ProfileSignal.EVIDENCE_QUALITY == "evidence_quality"
    assert ProfileSignal.REASONING_DEPTH == "reasoning_depth"
