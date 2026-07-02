# tests/services/feature_engine/test_feature_resolution_report.py

import pytest
from pydantic import ValidationError

from services.feature_engine.feature_resolution_report import (
    CandidateResolutionRecord,
    FeatureResolutionRecord,
    FeatureResolutionReport,
    ResolutionStrategy,
)


def _make_candidate_record(**kwargs) -> CandidateResolutionRecord:
    defaults = dict(
        updater_id="stub_updater",
        candidate_value="HIGH",
        candidate_confidence=0.8,
        source_observation_count=2,
    )
    defaults.update(kwargs)
    return CandidateResolutionRecord(**defaults)


def _make_resolution_record(**kwargs) -> FeatureResolutionRecord:
    defaults = dict(
        feature_type_id="reasoning_feature",
        strategy=ResolutionStrategy.SINGLE_CANDIDATE,
        final_value="HIGH",
        final_confidence=0.8,
    )
    defaults.update(kwargs)
    return FeatureResolutionRecord(**defaults)


def _make_report(**kwargs) -> FeatureResolutionReport:
    defaults = dict(
        session_id="sess-001",
        candidate_identity_id="cand-001",
        current_question_index=0,
    )
    defaults.update(kwargs)
    return FeatureResolutionReport(**defaults)


class TestResolutionStrategy:
    def test_all_strategies(self) -> None:
        assert ResolutionStrategy.SINGLE_CANDIDATE == "single_candidate"
        assert ResolutionStrategy.MERGED == "merged"
        assert ResolutionStrategy.REPLACED == "replaced"
        assert ResolutionStrategy.RETAINED == "retained"


class TestCandidateResolutionRecord:
    def test_valid(self) -> None:
        r = _make_candidate_record()
        assert r.updater_id == "stub_updater"

    def test_default_was_winner_false(self) -> None:
        assert _make_candidate_record().was_winner is False

    def test_default_was_superseded_false(self) -> None:
        assert _make_candidate_record().was_superseded is False

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate_record(candidate_confidence=1.5)

    def test_negative_obs_count_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate_record(source_observation_count=-1)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_candidate_record(unknown="x")

    def test_immutable(self) -> None:
        r = _make_candidate_record()
        with pytest.raises(ValidationError):
            r.candidate_value = "LOW"  # type: ignore[misc]


class TestFeatureResolutionRecord:
    def test_valid(self) -> None:
        r = _make_resolution_record()
        assert r.feature_type_id == "reasoning_feature"

    def test_with_candidate_records(self) -> None:
        cr = _make_candidate_record()
        r = _make_resolution_record(candidate_records=(cr,))
        assert len(r.candidate_records) == 1

    def test_default_policy_none(self) -> None:
        assert _make_resolution_record().policy_applied is None

    def test_with_policy_name(self) -> None:
        r = _make_resolution_record(policy_applied="DefaultMergePolicy")
        assert r.policy_applied == "DefaultMergePolicy"

    def test_empty_feature_type_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_resolution_record(feature_type_id="")

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_resolution_record(final_confidence=1.1)

    def test_all_strategies_accepted(self) -> None:
        for strategy in ResolutionStrategy:
            r = _make_resolution_record(strategy=strategy)
            assert r.strategy == strategy

    def test_immutable(self) -> None:
        r = _make_resolution_record()
        with pytest.raises(ValidationError):
            r.final_value = "LOW"  # type: ignore[misc]


class TestFeatureResolutionReport:
    def test_minimal_valid(self) -> None:
        report = _make_report()
        assert report.session_id == "sess-001"

    def test_default_counters_zero(self) -> None:
        report = _make_report()
        assert report.total_candidates_received == 0
        assert report.total_features_resolved == 0
        assert report.merge_resolutions == 0
        assert report.replace_resolutions == 0
        assert report.single_candidate_resolutions == 0
        assert report.retained_resolutions == 0

    def test_default_records_empty(self) -> None:
        assert _make_report().resolution_records == ()

    def test_with_resolution_records(self) -> None:
        record = _make_resolution_record()
        report = _make_report(
            total_candidates_received=1,
            total_features_resolved=1,
            single_candidate_resolutions=1,
            resolution_records=(record,),
        )
        assert len(report.resolution_records) == 1

    def test_negative_counter_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_report(total_candidates_received=-1)

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_report(session_id="")

    def test_default_schema_version(self) -> None:
        assert _make_report().schema_version == "1.0"

    def test_immutable(self) -> None:
        report = _make_report()
        with pytest.raises(ValidationError):
            report.session_id = "other"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_report(unknown="x")
