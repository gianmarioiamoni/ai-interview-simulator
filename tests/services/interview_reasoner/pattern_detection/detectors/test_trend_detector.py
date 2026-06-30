# tests/services/interview_reasoner/pattern_detection/detectors/test_trend_detector.py

import pytest
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.detectors.trend_detector import TrendDetector

from tests.services.interview_reasoner.pattern_detection.detectors.conftest import (
    make_input,
    make_dim_trace,
    make_reasoning_entry,
)

# ---- metadata ----

def test_metadata_name():
    assert TrendDetector().metadata.name == "TrendDetector"


def test_metadata_priority():
    assert TrendDetector().metadata.priority == 30


def test_metadata_depends_on_consistency():
    assert "ConsistencyDetector" in TrendDetector().metadata.dependencies


def test_metadata_enabled():
    assert TrendDetector().metadata.enabled is True


# ---- empty memory → no signals ----

def test_empty_memory_no_output():
    result = TrendDetector().detect(make_input())
    assert result.generated_signals == []


# ---- declining trend → REPEATED_WEAKNESS ----

def test_declining_trend_emits_weakness():
    trace = make_dim_trace(trend=Trend.DECLINING, evidence_count=3)
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    inp = make_input(memory=memory)
    result = TrendDetector().detect(inp)
    weakness = [e for e in result.generated_signals if e.signal_type == EvidenceType.REPEATED_WEAKNESS]
    assert len(weakness) == 1
    assert weakness[0].polarity == EvidencePolarity.NEGATIVE
    assert weakness[0].dimension == ProfileDimension.TECHNICAL_DEPTH


def test_declining_trend_strength_scales_with_evidence_count():
    trace_few = make_dim_trace(trend=Trend.DECLINING, evidence_count=1)
    trace_many = make_dim_trace(trend=Trend.DECLINING, evidence_count=10)
    profile_few = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace_few})
    profile_many = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace_many})
    r_few = TrendDetector().detect(make_input(memory=InterviewMemory(candidate_profile=profile_few)))
    r_many = TrendDetector().detect(make_input(memory=InterviewMemory(candidate_profile=profile_many)))
    s_few = r_few.generated_signals[0].strength
    s_many = r_many.generated_signals[0].strength
    assert s_many > s_few


# ---- improving trend → REPEATED_STRENGTH ----

def test_improving_trend_emits_strength():
    trace = make_dim_trace(trend=Trend.IMPROVING, evidence_count=3)
    profile = CandidateProfile(dimension_scores={ProfileDimension.COMMUNICATION: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    strength = [e for e in result.generated_signals if e.signal_type == EvidenceType.REPEATED_STRENGTH]
    assert len(strength) == 1
    assert strength[0].polarity == EvidencePolarity.POSITIVE
    assert strength[0].dimension == ProfileDimension.COMMUNICATION


def test_improving_trend_strength_scales_with_evidence_count():
    trace_few = make_dim_trace(trend=Trend.IMPROVING, evidence_count=1)
    trace_many = make_dim_trace(trend=Trend.IMPROVING, evidence_count=10)
    profile_few = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace_few})
    profile_many = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace_many})
    r_few = TrendDetector().detect(make_input(memory=InterviewMemory(candidate_profile=profile_few)))
    r_many = TrendDetector().detect(make_input(memory=InterviewMemory(candidate_profile=profile_many)))
    assert r_many.generated_signals[0].strength > r_few.generated_signals[0].strength


# ---- stable trend → REPEATED_STRENGTH at base strength ----

def test_stable_trend_emits_strength():
    trace = make_dim_trace(trend=Trend.STABLE)
    profile = CandidateProfile(dimension_scores={ProfileDimension.PROBLEM_SOLVING: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    sigs = [e for e in result.generated_signals if e.signal_type == EvidenceType.REPEATED_STRENGTH]
    assert len(sigs) == 1
    assert sigs[0].strength == 0.4  # _BASE_POSITIVE_STRENGTH


# ---- insufficient data → no signal ----

def test_insufficient_data_no_signal():
    trace = make_dim_trace(trend=Trend.INSUFFICIENT_DATA)
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    assert result.generated_signals == []


# ---- score volatility ----

def test_volatile_score_emits_confidence_drop():
    trace = make_dim_trace(trend=Trend.STABLE, average_score=60.0, last_score=80.0)  # deviation 20 > threshold 15
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert len(drops) == 1


def test_non_volatile_score_no_confidence_drop():
    trace = make_dim_trace(trend=Trend.STABLE, average_score=60.0, last_score=65.0)  # deviation 5 < threshold
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_no_last_score_skips_volatility():
    trace = make_dim_trace(trend=Trend.STABLE, last_score=None)
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_volatility_strength_capped_at_1():
    trace = make_dim_trace(trend=Trend.STABLE, average_score=0.0, last_score=100.0)  # max deviation
    profile = CandidateProfile(dimension_scores={ProfileDimension.TECHNICAL_DEPTH: trace})
    memory = InterviewMemory(candidate_profile=profile)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert all(e.strength <= 1.0 for e in drops)


# ---- session confidence drop ----

def test_session_confidence_drop_requires_4_entries():
    entries = [make_reasoning_entry(q_idx=i, reasoning_confidence=0.9) for i in range(3)]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_session_confidence_drop_detected():
    first = [make_reasoning_entry(q_idx=i, reasoning_confidence=0.9) for i in range(2)]
    second = [make_reasoning_entry(q_idx=i + 2, reasoning_confidence=0.5) for i in range(2)]
    history = ReasoningHistory(entries=first + second)
    memory = InterviewMemory(reasoning_history=history)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert len(drops) >= 1


def test_session_confidence_stable_no_drop():
    entries = [make_reasoning_entry(q_idx=i, reasoning_confidence=0.7) for i in range(4)]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert drops == []


def test_session_drop_uses_dominant_dim():
    first = [make_reasoning_entry(q_idx=i, dominant_dimension=ProfileDimension.COMMUNICATION, reasoning_confidence=0.9) for i in range(2)]
    second = [make_reasoning_entry(q_idx=i + 2, dominant_dimension=ProfileDimension.COMMUNICATION, reasoning_confidence=0.5) for i in range(2)]
    history = ReasoningHistory(entries=first + second)
    memory = InterviewMemory(reasoning_history=history)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert any(e.dimension == ProfileDimension.COMMUNICATION for e in drops)


def test_session_drop_fallback_to_technical_depth_when_no_dominant():
    first = [make_reasoning_entry(q_idx=i, dominant_dimension=None, reasoning_confidence=0.9) for i in range(2)]
    second = [make_reasoning_entry(q_idx=i + 2, dominant_dimension=None, reasoning_confidence=0.5) for i in range(2)]
    history = ReasoningHistory(entries=first + second)
    memory = InterviewMemory(reasoning_history=history)
    result = TrendDetector().detect(make_input(memory=memory))
    drops = [e for e in result.generated_signals if e.signal_type == EvidenceType.CONFIDENCE_DROP]
    assert any(e.dimension == ProfileDimension.TECHNICAL_DEPTH for e in drops)


def test_result_detector_name():
    result = TrendDetector().detect(make_input())
    assert result.detector_name == "TrendDetector"


def test_none_area_defaults_to_unknown():
    inp = ReasonerInput(session_id="s", question_index=0)
    result = TrendDetector().detect(inp)
    assert result.generated_signals == []
