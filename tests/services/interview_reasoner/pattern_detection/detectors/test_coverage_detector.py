# tests/services/interview_reasoner/pattern_detection/detectors/test_coverage_detector.py

import pytest
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from tests.domain.profile.profile_test_helpers import (
    candidate_profile_with_dimension_scores,
)
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.detectors.coverage_detector import CoverageDetector

from tests.services.interview_reasoner.pattern_detection.detectors.conftest import (
    make_input,
    make_signal,
    make_dim_trace,
)

ALL_DIMS = list(ProfileDimension)
N_DIMS = len(ALL_DIMS)

# ---- metadata ----

def test_metadata_name():
    assert CoverageDetector().metadata.name == "CoverageDetector"


def test_metadata_priority():
    assert CoverageDetector().metadata.priority == 10


def test_metadata_no_dependencies():
    assert CoverageDetector().metadata.dependencies == []


def test_metadata_enabled():
    assert CoverageDetector().metadata.enabled is True


# ---- empty memory → all dimensions missing ----

def test_empty_memory_flags_all_missing():
    inp = make_input()
    result = CoverageDetector().detect(inp)
    assert len(result.generated_signals) == N_DIMS
    types = {e.signal_type for e in result.generated_signals}
    assert types == {EvidenceType.MISSING_EVIDENCE}


def test_empty_memory_all_negative():
    inp = make_input()
    result = CoverageDetector().detect(inp)
    from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
    assert all(e.polarity == EvidencePolarity.NEGATIVE for e in result.generated_signals)


# ---- single evidence on one dim → others still missing ----

def test_one_dim_covered_rest_missing():
    sig = make_signal(dim=ProfileDimension.TECHNICAL_DEPTH)
    store = EvidenceStore(signals=[sig])
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory)
    result = CoverageDetector().detect(inp)
    # TECHNICAL_DEPTH has 1 signal (< threshold 2) → REPEATED_WEAKNESS
    # all other dims (4) have 0 → MISSING_EVIDENCE
    missing = [e for e in result.generated_signals if e.signal_type == EvidenceType.MISSING_EVIDENCE]
    weak = [e for e in result.generated_signals if e.signal_type == EvidenceType.REPEATED_WEAKNESS]
    assert len(missing) == N_DIMS - 1
    assert len(weak) == 1
    assert weak[0].dimension == ProfileDimension.TECHNICAL_DEPTH


def test_below_threshold_emits_repeated_weakness():
    sig = make_signal(dim=ProfileDimension.COMMUNICATION)
    store = EvidenceStore(signals=[sig])
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory)
    result = CoverageDetector().detect(inp)
    comm_sigs = [e for e in result.generated_signals if e.dimension == ProfileDimension.COMMUNICATION]
    assert len(comm_sigs) == 1
    assert comm_sigs[0].signal_type == EvidenceType.REPEATED_WEAKNESS


# ---- declining trend boosts strength ----

def test_declining_trend_boosts_strength():
    sig = make_signal(dim=ProfileDimension.PROBLEM_SOLVING)
    store = EvidenceStore(signals=[sig])
    trace = make_dim_trace(trend=Trend.DECLINING)
    profile = candidate_profile_with_dimension_scores({ProfileDimension.PROBLEM_SOLVING: trace})
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory, candidate_profile_v2=profile)
    result = CoverageDetector().detect(inp)
    ps_sigs = [e for e in result.generated_signals if e.dimension == ProfileDimension.PROBLEM_SOLVING]
    assert len(ps_sigs) == 1
    assert ps_sigs[0].strength > 0.5


def test_non_declining_trace_uses_base_strength():
    sig = make_signal(dim=ProfileDimension.PROBLEM_SOLVING)
    store = EvidenceStore(signals=[sig])
    trace = make_dim_trace(trend=Trend.STABLE)
    profile = candidate_profile_with_dimension_scores({ProfileDimension.PROBLEM_SOLVING: trace})
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory, candidate_profile_v2=profile)
    result = CoverageDetector().detect(inp)
    ps_sigs = [e for e in result.generated_signals if e.dimension == ProfileDimension.PROBLEM_SOLVING]
    assert ps_sigs[0].strength == 0.5  # _LOW_COVERAGE_SIGNAL_STRENGTH


# ---- fully covered dim → no signal emitted ----

def test_fully_covered_dim_no_signal():
    sigs = [make_signal(dim=ProfileDimension.TECHNICAL_DEPTH, q_idx=i) for i in range(3)]
    store = EvidenceStore(signals=sigs)
    memory = InterviewMemory(evidence_store=store)
    inp = make_input(memory=memory)
    result = CoverageDetector().detect(inp)
    td_sigs = [e for e in result.generated_signals if e.dimension == ProfileDimension.TECHNICAL_DEPTH]
    assert td_sigs == []


# ---- detector name in result ----

def test_result_detector_name():
    result = CoverageDetector().detect(make_input())
    assert result.detector_name == "CoverageDetector"


# ---- each signal uses correct question_index and area ----

def test_signals_carry_correct_metadata():
    inp = make_input(question_index=7, area="system_design")
    result = CoverageDetector().detect(inp)
    for e in result.generated_signals:
        assert e.question_index == 7
        assert e.question_area == "system_design"


# ---- fallback area ----

def test_none_area_defaults_to_unknown():
    inp = ReasonerInput(session_id="s", question_index=0)
    result = CoverageDetector().detect(inp)
    for e in result.generated_signals:
        assert e.question_area == "unknown"
