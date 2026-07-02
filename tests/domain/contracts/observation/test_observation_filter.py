# tests/domain/contracts/observation/test_observation_filter.py

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class TestObservationFilterDefaults:
    def test_all_fields_none_by_default(self):
        f = ObservationFilter()
        assert f.observation_types is None
        assert f.statuses is None
        assert f.origins is None
        assert f.question_index_min is None
        assert f.question_index_max is None
        assert f.observed_after is None
        assert f.observed_before is None
        assert f.confidence_min is None
        assert f.confidence_max is None
        assert f.weight_min is None
        assert f.weight_max is None
        assert f.tags_any is None
        assert f.tags_all is None
        assert f.session_id is None

    def test_schema_version_default(self):
        assert ObservationFilter().schema_version == "1.0"


class TestObservationFilterImmutability:
    def test_frozen(self):
        f = ObservationFilter()
        with pytest.raises(ValidationError):
            f.session_id = "new"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationFilter(extra_field="x")  # type: ignore[call-arg]


class TestObservationFilterRangeValidation:
    def test_question_index_min_gt_max_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(question_index_min=5, question_index_max=3)

    def test_question_index_min_eq_max_valid(self):
        f = ObservationFilter(question_index_min=3, question_index_max=3)
        assert f.question_index_min == 3

    def test_question_index_only_min_valid(self):
        f = ObservationFilter(question_index_min=0)
        assert f.question_index_min == 0

    def test_question_index_negative_min_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(question_index_min=-1)

    def test_observed_after_ge_before_raises(self):
        now = _now()
        with pytest.raises(ValidationError):
            ObservationFilter(observed_after=now, observed_before=now)

    def test_observed_after_gt_before_raises(self):
        now = _now()
        with pytest.raises(ValidationError):
            ObservationFilter(observed_after=now + timedelta(seconds=1), observed_before=now)

    def test_observed_after_lt_before_valid(self):
        now = _now()
        f = ObservationFilter(observed_after=now - timedelta(minutes=5), observed_before=now)
        assert f.observed_after < f.observed_before

    def test_confidence_min_gt_max_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(confidence_min=0.8, confidence_max=0.2)

    def test_confidence_min_eq_max_valid(self):
        f = ObservationFilter(confidence_min=0.5, confidence_max=0.5)
        assert f.confidence_min == 0.5

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(confidence_min=-0.1)

    def test_weight_min_gt_max_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(weight_min=0.9, weight_max=0.1)

    def test_weight_min_zero_raises(self):
        with pytest.raises(ValidationError):
            ObservationFilter(weight_min=0.0)


class TestObservationFilterFields:
    def test_observation_types_set(self):
        f = ObservationFilter(
            observation_types=frozenset({ObservationType.TECHNICAL_CORRECTNESS})
        )
        assert ObservationType.TECHNICAL_CORRECTNESS in f.observation_types

    def test_statuses_set(self):
        f = ObservationFilter(statuses=frozenset({ObservationStatus.ACTIVE}))
        assert ObservationStatus.ACTIVE in f.statuses

    def test_origins_set(self):
        f = ObservationFilter(origins=frozenset({ObservationOrigin.EVALUATION}))
        assert ObservationOrigin.EVALUATION in f.origins

    def test_tags_any_set(self):
        f = ObservationFilter(tags_any=frozenset({"python", "senior"}))
        assert "python" in f.tags_any

    def test_tags_all_set(self):
        f = ObservationFilter(tags_all=frozenset({"python"}))
        assert "python" in f.tags_all

    def test_session_id_set(self):
        f = ObservationFilter(session_id="sess-xyz")
        assert f.session_id == "sess-xyz"
