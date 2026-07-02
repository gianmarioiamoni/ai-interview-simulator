# tests/domain/contracts/observation/extraction/test_observation_extraction_result.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_extraction_diagnostics import ObservationExtractionDiagnostics
from domain.contracts.observation.extraction.observation_extraction_result import ObservationExtractionResult
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_type import ObservationType


def _diag(question_index: int = 0, session_id: str = "s") -> ObservationExtractionDiagnostics:
    return ObservationExtractionDiagnostics(question_index=question_index, session_id=session_id)


def _obs(question_index: int = 0, otype: ObservationType = ObservationType.TECHNICAL_CORRECTNESS) -> Observation:
    meta = ObservationMetadata(
        question_index=question_index,
        session_id="s",
        origin=ObservationOrigin.EVIDENCE_SIGNAL,
        source_ref="rule-001",
    )
    return Observation(
        observation_type=otype,
        metadata=meta,
        description="test observation",
        confidence=0.8,
    )


class TestObservationExtractionResultDefaults:
    def test_observations_default_empty(self):
        r = ObservationExtractionResult(
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.observations == ()

    def test_schema_version_default(self):
        r = ObservationExtractionResult(
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.schema_version == "1.0"


class TestObservationExtractionResultImmutability:
    def test_frozen(self):
        r = ObservationExtractionResult(
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        with pytest.raises(ValidationError):
            r.question_index = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationExtractionResult(
                question_index=0,
                session_id="s",
                diagnostics=_diag(),
                extra="x",  # type: ignore[call-arg]
            )


class TestObservationExtractionResultValidation:
    def test_negative_question_index_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionResult(
                question_index=-1,
                session_id="s",
                diagnostics=_diag(),
            )

    def test_empty_session_id_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionResult(
                question_index=0,
                session_id="",
                diagnostics=_diag(),
            )


class TestObservationExtractionResultProperties:
    def test_observation_count_empty(self):
        r = ObservationExtractionResult(
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.observation_count == 0

    def test_is_empty_true_when_no_observations(self):
        r = ObservationExtractionResult(
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.is_empty is True

    def test_observation_count_with_observations(self):
        r = ObservationExtractionResult(
            observations=(_obs(), _obs(otype=ObservationType.COMMUNICATION_CLEAR)),
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.observation_count == 2

    def test_is_empty_false_with_observations(self):
        r = ObservationExtractionResult(
            observations=(_obs(),),
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert r.is_empty is False

    def test_observations_is_tuple(self):
        r = ObservationExtractionResult(
            observations=(_obs(),),
            question_index=0,
            session_id="s",
            diagnostics=_diag(),
        )
        assert isinstance(r.observations, tuple)
