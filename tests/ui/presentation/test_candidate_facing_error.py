# tests/ui/presentation/test_candidate_facing_error.py
# EPIC-07 P1/C1 — AsyncBoundary closed set; catalog key→text; I-CF / DM-V-CF-01.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    AsyncBoundary,
    CANDIDATE_FACING_ERROR_CATALOG,
    CandidateFacingError,
    get_candidate_facing_error_entry,
)

_EXPECTED_BOUNDARIES = (
    AsyncBoundary.SESSION_START,
    AsyncBoundary.ANSWER_SUBMIT,
    AsyncBoundary.NEXT_OR_REPORT,
    AsyncBoundary.REPORT_EXPORT,
    AsyncBoundary.REPLAY_ENTER,
    AsyncBoundary.SESSION_HISTORY_LOAD,
)

_EXPECTED_KEYS = (
    "err.session_start.failed",
    "err.answer_submit.failed",
    "err.next_or_report.failed",
    "err.report_export.failed",
    "err.replay_enter.failed",
    "err.session_history_load.failed",
)


class TestAsyncBoundaryClosed:
    def test_enum_member_count_is_six(self) -> None:
        assert len(AsyncBoundary) == 6

    def test_enum_members_match_frozen_set(self) -> None:
        assert tuple(AsyncBoundary) == _EXPECTED_BOUNDARIES

    def test_enum_values_are_stable_names(self) -> None:
        assert {member.value for member in AsyncBoundary} == {
            member.name for member in AsyncBoundary
        }


class TestCandidateFacingErrorCatalog:
    def test_catalog_covers_all_keys(self) -> None:
        assert set(CANDIDATE_FACING_ERROR_CATALOG) == set(_EXPECTED_KEYS)

    def test_catalog_covers_each_async_boundary_exactly_once(self) -> None:
        boundaries = [entry.boundary for entry in CANDIDATE_FACING_ERROR_CATALOG.values()]
        assert sorted(boundaries, key=lambda b: b.value) == sorted(
            _EXPECTED_BOUNDARIES, key=lambda b: b.value
        )

    @pytest.mark.parametrize("message_key", _EXPECTED_KEYS)
    def test_catalog_key_maps_to_non_empty_message_text(self, message_key: str) -> None:
        entry = get_candidate_facing_error_entry(message_key)
        assert entry.message_key == message_key
        assert entry.message_text
        assert entry.is_retryable is True

    def test_unknown_key_fails_fast(self) -> None:
        with pytest.raises(ValueError, match="SM-06"):
            get_candidate_facing_error_entry("err.unknown.failed")


class TestCandidateFacingErrorContracts:
    @pytest.mark.parametrize("message_key", _EXPECTED_KEYS)
    def test_from_catalog_message_text_equals_catalog(self, message_key: str) -> None:
        entry = get_candidate_facing_error_entry(message_key)
        error = CandidateFacingError.from_catalog(message_key)
        assert error.message_key == entry.message_key
        assert error.message_text == entry.message_text
        assert error.boundary == entry.boundary
        assert error.is_retryable == entry.is_retryable
        assert error.correlation_token is None

    def test_direct_construction_enforces_message_equality(self) -> None:
        entry = get_candidate_facing_error_entry("err.session_start.failed")
        with pytest.raises(ValidationError, match="DM-V-CF-01"):
            CandidateFacingError(
                boundary=entry.boundary,
                message_key=entry.message_key,
                message_text="Internal stack leaked.",
                is_retryable=entry.is_retryable,
            )

    def test_boundary_mismatch_rejected(self) -> None:
        entry = get_candidate_facing_error_entry("err.session_start.failed")
        with pytest.raises(ValidationError, match="DM-V-CF-01"):
            CandidateFacingError(
                boundary=AsyncBoundary.ANSWER_SUBMIT,
                message_key=entry.message_key,
                message_text=entry.message_text,
                is_retryable=entry.is_retryable,
            )

    def test_immutable_after_construction(self) -> None:
        error = CandidateFacingError.from_catalog("err.report_export.failed")
        with pytest.raises(ValidationError):
            error.message_text = "mutated"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        entry = get_candidate_facing_error_entry("err.answer_submit.failed")
        with pytest.raises(ValidationError):
            CandidateFacingError(
                boundary=entry.boundary,
                message_key=entry.message_key,
                message_text=entry.message_text,
                is_retryable=entry.is_retryable,
                failure_reason="ValueError: boom",  # type: ignore[call-arg]
            )

    def test_correlation_token_rejects_traceback_and_py_paths(self) -> None:
        with pytest.raises(ValidationError):
            CandidateFacingError.from_catalog(
                "err.replay_enter.failed",
                correlation_token="Traceback (most recent call last)",
            )
        with pytest.raises(ValidationError):
            CandidateFacingError.from_catalog(
                "err.replay_enter.failed",
                correlation_token="app/ui/handlers/start_handler.py:12",
            )

    def test_correlation_token_accepts_opaque_token(self) -> None:
        error = CandidateFacingError.from_catalog(
            "err.session_history_load.failed",
            correlation_token="corr-abc-123",
        )
        assert error.correlation_token == "corr-abc-123"
