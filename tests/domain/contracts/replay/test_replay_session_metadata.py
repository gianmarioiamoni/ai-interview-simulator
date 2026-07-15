# tests/domain/contracts/replay/test_replay_session_metadata.py
# EPIC-03 Phase 2b — ReplaySessionMetadata contract tests.

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata


SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def _make(**overrides) -> ReplaySessionMetadata:
    defaults = dict(
        interview_index=1,
        session_date=SESSION_DATE,
        role="Software Engineer",
        seniority_level="Senior",
        interview_mode="technical",
        question_count=5,
        session_duration_seconds=None,
        company=None,
    )
    defaults.update(overrides)
    return ReplaySessionMetadata(**defaults)


class TestReplaySessionMetadataConstruction:

    def test_minimal_required_fields(self):
        meta = _make()
        assert meta.interview_index == 1
        assert meta.session_date == SESSION_DATE
        assert meta.role == "Software Engineer"
        assert meta.seniority_level == "Senior"
        assert meta.interview_mode == "technical"
        assert meta.question_count == 5
        assert meta.session_duration_seconds is None
        assert meta.company is None

    def test_with_optional_fields(self):
        meta = _make(session_duration_seconds=1200.5, company="Acme Corp")
        assert meta.session_duration_seconds == 1200.5
        assert meta.company == "Acme Corp"

    def test_question_count_zero_accepted(self):
        meta = _make(question_count=0)
        assert meta.question_count == 0

    def test_interview_index_one_accepted(self):
        meta = _make(interview_index=1)
        assert meta.interview_index == 1

    def test_interview_index_large_value(self):
        meta = _make(interview_index=100)
        assert meta.interview_index == 100


class TestReplaySessionMetadataImmutability:

    def test_frozen_raises_on_mutation(self):
        meta = _make()
        with pytest.raises((ValidationError, TypeError)):
            meta.role = "changed"

    def test_frozen_raises_on_index_mutation(self):
        meta = _make()
        with pytest.raises((ValidationError, TypeError)):
            meta.interview_index = 99

    def test_frozen_raises_on_count_mutation(self):
        meta = _make()
        with pytest.raises((ValidationError, TypeError)):
            meta.question_count = 99


class TestReplaySessionMetadataExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ReplaySessionMetadata(
                interview_index=1,
                session_date=SESSION_DATE,
                role="Engineer",
                seniority_level="Mid",
                interview_mode="technical",
                question_count=3,
                unknown_field="bad",  # type: ignore[call-arg]
            )


class TestReplaySessionMetadataFieldConstraints:

    def test_interview_index_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make(interview_index=0)

    def test_interview_index_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make(interview_index=-1)

    def test_question_count_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make(question_count=-1)

    def test_role_empty_rejected(self):
        with pytest.raises(ValidationError):
            _make(role="")

    def test_seniority_level_empty_rejected(self):
        with pytest.raises(ValidationError):
            _make(seniority_level="")

    def test_interview_mode_empty_rejected(self):
        with pytest.raises(ValidationError):
            _make(interview_mode="")
