# tests/domain/contracts/reasoning/test_misc_contracts.py
"""Covers: CandidateProfile, CoverageState, ReasoningHistory, SessionMetrics,
ReasoningConfidence, FollowUpRecommendation, NavigationRecommendation,
ReasoningBasis, DetectorContext, DetectorResult, SignalTrace, ReasoningEntry."""

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.coverage_state import CoverageState
from domain.contracts.reasoning.reasoning_history import ReasoningHistory, ReasoningEntry
from domain.contracts.reasoning.session_metrics import SessionMetrics
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
from domain.contracts.reasoning.follow_up_recommendation import FollowUpRecommendation
from domain.contracts.reasoning.navigation_recommendation import NavigationRecommendation
from domain.contracts.reasoning.reasoning_basis import ReasoningBasis
from domain.contracts.reasoning.detector_context import DetectorContext, DetectorResult
from domain.contracts.reasoning.signal_trace import SignalTrace, SignalObservation
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.data_sufficiency import DataSufficiency
from domain.contracts.reasoning.trend import Trend
from domain.contracts.reasoning.profile_dimension import ProfileDimension


# --- CandidateProfile ---

def test_candidate_profile_defaults():
    cp = CandidateProfile()
    assert cp.dimension_scores == {}
    assert cp.signals == {}
    assert cp.questions_answered == 0
    assert cp.areas_covered == []
    assert cp.last_updated_at_question_index == -1


def test_candidate_profile_immutable():
    cp = CandidateProfile()
    with pytest.raises((ValidationError, TypeError)):
        cp.questions_answered = 1


def test_candidate_profile_extra_forbidden():
    with pytest.raises(ValidationError):
        CandidateProfile(scores=[1, 2, 3])


# --- CoverageState ---

def test_coverage_state_defaults():
    cs = CoverageState()
    assert cs.covered_areas == []
    assert cs.coverage_depth == {}
    assert cs.follow_up_history == []
    assert cs.repeated_topics == []


def test_coverage_state_immutable():
    cs = CoverageState()
    with pytest.raises((ValidationError, TypeError)):
        cs.covered_areas = ["area"]


# --- ReasoningEntry ---

def test_reasoning_entry_defaults():
    entry = ReasoningEntry(question_index=2)
    assert entry.dominant_dimension is None
    assert entry.detected_patterns == []
    assert entry.follow_up_recommended is False
    assert entry.schema_version == "1.0"


def test_reasoning_entry_immutable():
    entry = ReasoningEntry(question_index=0)
    with pytest.raises((ValidationError, TypeError)):
        entry.follow_up_recommended = True


def test_reasoning_entry_negative_index_rejected():
    with pytest.raises(ValidationError):
        ReasoningEntry(question_index=-1)


# --- ReasoningHistory ---

def test_reasoning_history_defaults():
    rh = ReasoningHistory()
    assert rh.entries == []


def test_reasoning_history_capacity():
    from domain.contracts.reasoning.reasoning_history import _MAX_ENTRIES
    entries = [ReasoningEntry(question_index=i) for i in range(_MAX_ENTRIES)]
    rh = ReasoningHistory(entries=entries)
    assert len(rh.entries) == _MAX_ENTRIES
    with pytest.raises(ValidationError):
        ReasoningHistory(entries=entries + [ReasoningEntry(question_index=_MAX_ENTRIES)])


# --- SessionMetrics ---

def test_session_metrics_defaults():
    sm = SessionMetrics()
    assert sm.questions_answered == 0
    assert sm.follow_up_count == 0
    assert sm.last_reasoning_at_question_index is None


def test_session_metrics_negative_rejected():
    with pytest.raises(ValidationError):
        SessionMetrics(questions_answered=-1)


# --- ReasoningConfidence ---

def test_reasoning_confidence_defaults():
    rc = ReasoningConfidence()
    assert rc.reasoning_confidence == 0.0
    assert rc.evidence_strength == 0.0
    assert rc.data_sufficiency == DataSufficiency.INSUFFICIENT


def test_reasoning_confidence_bounds():
    with pytest.raises(ValidationError):
        ReasoningConfidence(reasoning_confidence=1.1)
    with pytest.raises(ValidationError):
        ReasoningConfidence(evidence_strength=-0.01)


# --- FollowUpRecommendation ---

def test_follow_up_recommendation_recommended_false():
    rec = FollowUpRecommendation(recommended=False)
    assert rec.priority == 2
    assert rec.trigger_types == []


def test_follow_up_recommendation_priority_bounds():
    with pytest.raises(ValidationError):
        FollowUpRecommendation(recommended=True, priority=0)
    with pytest.raises(ValidationError):
        FollowUpRecommendation(recommended=True, priority=4)


# --- NavigationRecommendation ---

def test_navigation_recommendation_defaults():
    rec = NavigationRecommendation()
    assert rec.suggested_area is None
    assert rec.deepen_current is False
    assert rec.skip_area is None


# --- ReasoningBasis ---

def test_reasoning_basis_defaults():
    rb = ReasoningBasis()
    assert rb.dominant_dimension is None
    assert rb.session_quality_trend == Trend.INSUFFICIENT_DATA
    assert rb.detected_patterns == []


# --- SignalObservation / SignalTrace ---

def test_signal_observation_basic():
    obs = SignalObservation(
        question_index=1,
        polarity=EvidencePolarity.POSITIVE,
        evidence="demonstrated clear trade-off reasoning",
    )
    assert obs.question_index == 1


def test_signal_observation_empty_evidence_rejected():
    with pytest.raises(ValidationError):
        SignalObservation(question_index=0, polarity=EvidencePolarity.NEGATIVE, evidence="")


def test_signal_trace_defaults():
    st = SignalTrace()
    assert st.observations == []
    assert st.trend == Trend.INSUFFICIENT_DATA


def test_signal_trace_capacity():
    from domain.contracts.reasoning.signal_trace import _MAX_OBSERVATIONS
    obs = SignalObservation(
        question_index=0, polarity=EvidencePolarity.NEGATIVE, evidence="x"
    )
    observations = [
        SignalObservation(question_index=i, polarity=EvidencePolarity.NEGATIVE, evidence="x")
        for i in range(_MAX_OBSERVATIONS)
    ]
    st = SignalTrace(observations=observations)
    assert len(st.observations) == _MAX_OBSERVATIONS
    with pytest.raises(ValidationError):
        SignalTrace(observations=observations + [obs])


# --- DetectorContext / DetectorResult ---

def test_detector_context_basic():
    inp = ReasonerInput(session_id="s", question_index=0)
    ctx = DetectorContext(detector_name="ReasoningDepthDetector", input=inp)
    assert ctx.detector_name == "ReasoningDepthDetector"


def test_detector_result_defaults():
    result = DetectorResult(detector_name="KnowledgeConsistencyDetector")
    assert result.generated_signals == []
    assert result.matches == []
    assert result.warnings == []
    assert result.execution_time_ms == 0.0


def test_detector_result_negative_time_rejected():
    with pytest.raises(ValidationError):
        DetectorResult(detector_name="X", execution_time_ms=-1.0)
