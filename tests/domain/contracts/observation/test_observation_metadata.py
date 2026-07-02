# tests/domain/contracts/observation/test_observation_metadata.py

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin


def _runtime_meta(**kwargs) -> ObservationMetadata:
    defaults = dict(
        question_index=0,
        session_id="sess-001",
        origin=ObservationOrigin.EVALUATION,
        source_ref="eval-abc",
    )
    defaults.update(kwargs)
    return ObservationMetadata(**defaults)


class TestObservationMetadataDefaults:
    def test_observed_at_defaults_to_utcnow(self):
        meta = _runtime_meta()
        assert meta.observed_at.tzinfo is not None

    def test_extractor_version_default(self):
        meta = _runtime_meta()
        assert meta.extractor_version == "1.0"

    def test_schema_version_default(self):
        meta = _runtime_meta()
        assert meta.schema_version == "1.0"

    def test_source_ref_stored(self):
        meta = _runtime_meta(source_ref="ref-123")
        assert meta.source_ref == "ref-123"

    def test_session_id_stored(self):
        meta = _runtime_meta(session_id="my-session")
        assert meta.session_id == "my-session"

    def test_question_index_stored(self):
        meta = _runtime_meta(question_index=5)
        assert meta.question_index == 5


class TestObservationMetadataImmutability:
    def test_frozen(self):
        meta = _runtime_meta()
        with pytest.raises(ValidationError):
            meta.question_index = 99

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationMetadata(
                question_index=0,
                session_id="s",
                origin=ObservationOrigin.EVALUATION,
                source_ref="r",
                unexpected="x",  # type: ignore[call-arg]
            )


class TestObservationMetadataValidation:
    def test_negative_question_index_raises(self):
        with pytest.raises(ValidationError):
            _runtime_meta(question_index=-1)

    def test_empty_session_id_raises(self):
        with pytest.raises(ValidationError):
            _runtime_meta(session_id="")

    def test_runtime_origin_requires_source_ref(self):
        for origin in [ObservationOrigin.EVALUATION, ObservationOrigin.EVIDENCE_SIGNAL, ObservationOrigin.PATTERN_DETECTOR]:
            with pytest.raises(ValidationError):
                ObservationMetadata(
                    question_index=0,
                    session_id="s",
                    origin=origin,
                    source_ref=None,
                )

    def test_replay_origin_allows_no_source_ref(self):
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.REPLAY,
            source_ref=None,
        )
        assert meta.source_ref is None

    def test_calibration_origin_allows_no_source_ref(self):
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.CALIBRATION,
            source_ref=None,
        )
        assert meta.source_ref is None

    def test_naive_datetime_gets_utc_timezone(self):
        naive = datetime(2026, 1, 1, 12, 0, 0)
        meta = ObservationMetadata(
            observed_at=naive,
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.REPLAY,
        )
        assert meta.observed_at.tzinfo == timezone.utc

    def test_aware_datetime_preserved(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        meta = _runtime_meta(observed_at=dt)
        assert meta.observed_at == dt

    def test_iso_string_parsed(self):
        meta = ObservationMetadata(
            observed_at="2026-01-01T10:00:00+00:00",
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.REPLAY,
        )
        assert meta.observed_at.year == 2026

    def test_question_index_zero_valid(self):
        meta = _runtime_meta(question_index=0)
        assert meta.question_index == 0

    def test_large_question_index_valid(self):
        meta = _runtime_meta(question_index=999)
        assert meta.question_index == 999
