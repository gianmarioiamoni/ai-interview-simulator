# tests/domain/contracts/observation/extraction/test_observation_extraction_context.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from tests.domain.contracts.observation.extraction.conftest import make_signal


class TestObservationExtractionContextDefaults:
    def test_extractor_version_default(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(0),),
            question_index=0,
            session_id="s",
        )
        assert ctx.extractor_version == "1.0"

    def test_schema_version_default(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(0),),
            question_index=0,
            session_id="s",
        )
        assert ctx.schema_version == "1.0"


class TestObservationExtractionContextImmutability:
    def test_frozen(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(0),),
            question_index=0,
            session_id="s",
        )
        with pytest.raises(ValidationError):
            ctx.question_index = 5

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationExtractionContext(
                signals=(make_signal(0),),
                question_index=0,
                session_id="s",
                extra="x",  # type: ignore[call-arg]
            )


class TestObservationExtractionContextValidation:
    def test_empty_signals_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionContext(
                signals=(),
                question_index=0,
                session_id="s",
            )

    def test_negative_question_index_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionContext(
                signals=(make_signal(0),),
                question_index=-1,
                session_id="s",
            )

    def test_empty_session_id_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionContext(
                signals=(make_signal(0),),
                question_index=0,
                session_id="",
            )

    def test_signal_question_index_mismatch_raises(self):
        with pytest.raises(ValidationError):
            ObservationExtractionContext(
                signals=(make_signal(question_index=5),),
                question_index=0,
                session_id="s",
            )

    def test_multiple_signals_same_question_index_valid(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(3), make_signal(3)),
            question_index=3,
            session_id="s",
        )
        assert len(ctx.signals) == 2

    def test_signals_stored_as_tuple(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(0),),
            question_index=0,
            session_id="s",
        )
        assert isinstance(ctx.signals, tuple)

    def test_signals_from_list_accepted(self):
        ctx = ObservationExtractionContext(
            signals=[make_signal(0)],  # type: ignore[arg-type]
            question_index=0,
            session_id="s",
        )
        assert len(ctx.signals) == 1

    def test_question_index_zero_valid(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(0),),
            question_index=0,
            session_id="s",
        )
        assert ctx.question_index == 0

    def test_large_question_index_valid(self):
        ctx = ObservationExtractionContext(
            signals=(make_signal(99),),
            question_index=99,
            session_id="s",
        )
        assert ctx.question_index == 99
