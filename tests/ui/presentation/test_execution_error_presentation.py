# tests/ui/presentation/test_execution_error_presentation.py
# EPIC-07 P4/C7 — ExecutionErrorPresentation projector; traceback ban.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    EXECUTION_ERROR_CATALOG,
    ExecutionErrorKind,
    ExecutionErrorPresentation,
    classify_execution_error_kind,
    get_execution_error_entry,
    project_execution_error,
)

_EXPECTED_KINDS = (
    ExecutionErrorKind.SYNTAX,
    ExecutionErrorKind.RUNTIME,
    ExecutionErrorKind.SQL,
    ExecutionErrorKind.TEST_FAILURE,
    ExecutionErrorKind.UNKNOWN_SAFE,
)


class TestExecutionErrorKindClosed:
    def test_enum_member_count_is_five(self) -> None:
        assert len(ExecutionErrorKind) == 5

    def test_enum_members_match_frozen_set(self) -> None:
        assert tuple(ExecutionErrorKind) == _EXPECTED_KINDS


class TestExecutionErrorCatalog:
    def test_catalog_covers_all_kinds(self) -> None:
        assert set(EXECUTION_ERROR_CATALOG) == set(_EXPECTED_KINDS)

    @pytest.mark.parametrize("kind", _EXPECTED_KINDS)
    def test_kind_maps_to_non_empty_catalog_message(self, kind: ExecutionErrorKind) -> None:
        entry = get_execution_error_entry(kind)
        assert entry.kind == kind
        assert entry.candidate_message


class TestExecutionErrorPresentationContracts:
    @pytest.mark.parametrize("kind", _EXPECTED_KINDS)
    def test_from_kind_uses_catalog_and_bans_traceback(
        self, kind: ExecutionErrorKind
    ) -> None:
        presentation = ExecutionErrorPresentation.from_kind(kind)
        entry = get_execution_error_entry(kind)
        assert presentation.kind == kind
        assert presentation.candidate_message == entry.candidate_message
        assert presentation.shows_traceback is False
        assert presentation.detail_lines == ()

    def test_shows_traceback_true_rejected(self) -> None:
        entry = get_execution_error_entry(ExecutionErrorKind.SYNTAX)
        with pytest.raises(ValidationError):
            ExecutionErrorPresentation(
                kind=ExecutionErrorKind.SYNTAX,
                candidate_message=entry.candidate_message,
                shows_traceback=True,  # type: ignore[arg-type]
            )

    def test_candidate_message_must_match_catalog(self) -> None:
        with pytest.raises(ValidationError, match="DM-V-EX"):
            ExecutionErrorPresentation(
                kind=ExecutionErrorKind.SYNTAX,
                candidate_message="SyntaxError: invalid syntax",
                shows_traceback=False,
            )

    def test_detail_lines_reject_traceback_path_and_exception_class(self) -> None:
        with pytest.raises(ValidationError, match="I-EX-01"):
            ExecutionErrorPresentation.from_kind(
                ExecutionErrorKind.TEST_FAILURE,
                detail_lines=("Traceback (most recent call last):",),
            )
        with pytest.raises(ValidationError, match="I-EX-01"):
            ExecutionErrorPresentation.from_kind(
                ExecutionErrorKind.TEST_FAILURE,
                detail_lines=("/Users/dev/project/app/main.py line 12",),
            )
        with pytest.raises(ValidationError, match="I-EX-01"):
            ExecutionErrorPresentation.from_kind(
                ExecutionErrorKind.TEST_FAILURE,
                detail_lines=("ValueError: boom",),
            )

    def test_test_failure_allows_candidate_safe_detail_lines(self) -> None:
        presentation = ExecutionErrorPresentation.from_kind(
            ExecutionErrorKind.TEST_FAILURE,
            detail_lines=("Test case: empty input", "Test case: large list"),
        )
        assert presentation.detail_lines == (
            "Test case: empty input",
            "Test case: large list",
        )
        assert presentation.shows_traceback is False


class TestProjectExecutionError:
    def test_structured_kind_wins(self) -> None:
        presentation = project_execution_error(
            structured_kind=ExecutionErrorKind.SQL,
            raw_error="SyntaxError: ignored when structured",
        )
        assert presentation.kind is ExecutionErrorKind.SQL
        assert presentation.candidate_message == get_execution_error_entry(
            ExecutionErrorKind.SQL
        ).candidate_message
        assert presentation.shows_traceback is False

    def test_raw_error_never_leaks_into_message(self) -> None:
        raw = (
            "Traceback (most recent call last):\n"
            '  File "/tmp/sandbox/main.py", line 3, in <module>\n'
            "NameError: name 'x' is not defined"
        )
        presentation = project_execution_error(raw_error=raw)
        assert presentation.kind is ExecutionErrorKind.RUNTIME
        assert "Traceback" not in presentation.candidate_message
        assert ".py" not in presentation.candidate_message
        assert "NameError" not in presentation.candidate_message
        assert presentation.candidate_message == get_execution_error_entry(
            ExecutionErrorKind.RUNTIME
        ).candidate_message

    def test_insufficient_detail_uses_unknown_safe(self) -> None:
        presentation = project_execution_error(raw_error="")
        assert presentation.kind is ExecutionErrorKind.UNKNOWN_SAFE
        assert presentation.candidate_message == get_execution_error_entry(
            ExecutionErrorKind.UNKNOWN_SAFE
        ).candidate_message

    def test_has_test_failures_projects_test_failure(self) -> None:
        presentation = project_execution_error(
            has_test_failures=True,
            detail_lines=("case A",),
        )
        assert presentation.kind is ExecutionErrorKind.TEST_FAILURE
        assert presentation.detail_lines == ("case A",)

    def test_non_test_failure_drops_detail_lines(self) -> None:
        presentation = project_execution_error(
            structured_kind=ExecutionErrorKind.SYNTAX,
            detail_lines=("case A",),
        )
        assert presentation.detail_lines == ()

    @pytest.mark.parametrize(
        ("raw_error", "expected"),
        [
            ("SyntaxError: invalid syntax", ExecutionErrorKind.SYNTAX),
            ("OperationalError: near SELECT", ExecutionErrorKind.SQL),
            ("TypeError: unsupported operand", ExecutionErrorKind.RUNTIME),
            ("something opaque failed", ExecutionErrorKind.UNKNOWN_SAFE),
        ],
    )
    def test_classify_from_raw_error(
        self, raw_error: str, expected: ExecutionErrorKind
    ) -> None:
        assert classify_execution_error_kind(raw_error=raw_error) is expected
