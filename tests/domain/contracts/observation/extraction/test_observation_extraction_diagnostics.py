# tests/domain/contracts/observation/extraction/test_observation_extraction_diagnostics.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_extraction_diagnostics import (
    ObservationExtractionDiagnostics,
    ObservationRuleDiagnostic,
)


class TestObservationRuleDiagnosticDefaults:
    def test_evaluated_default_true(self):
        d = ObservationRuleDiagnostic(rule_id="r")
        assert d.evaluated is True

    def test_skipped_default_false(self):
        d = ObservationRuleDiagnostic(rule_id="r")
        assert d.skipped is False

    def test_match_count_default_zero(self):
        d = ObservationRuleDiagnostic(rule_id="r")
        assert d.match_count == 0

    def test_error_message_default_none(self):
        d = ObservationRuleDiagnostic(rule_id="r")
        assert d.error_message is None


class TestObservationRuleDiagnosticImmutability:
    def test_frozen(self):
        d = ObservationRuleDiagnostic(rule_id="r")
        with pytest.raises(ValidationError):
            d.match_count = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationRuleDiagnostic(rule_id="r", extra="x")  # type: ignore[call-arg]


class TestObservationRuleDiagnosticValidation:
    def test_empty_rule_id_raises(self):
        with pytest.raises(ValidationError):
            ObservationRuleDiagnostic(rule_id="")

    def test_negative_match_count_raises(self):
        with pytest.raises(ValidationError):
            ObservationRuleDiagnostic(rule_id="r", match_count=-1)

    def test_error_message_stored(self):
        d = ObservationRuleDiagnostic(rule_id="r", error_message="boom")
        assert d.error_message == "boom"


class TestObservationExtractionDiagnosticsDefaults:
    def test_schema_version_default(self):
        d = ObservationExtractionDiagnostics(question_index=0, session_id="s")
        assert d.schema_version == "1.0"

    def test_all_counts_default_zero(self):
        d = ObservationExtractionDiagnostics(question_index=0, session_id="s")
        assert d.rules_evaluated == 0
        assert d.rules_skipped == 0
        assert d.rules_errored == 0
        assert d.total_matches == 0

    def test_rule_diagnostics_default_empty(self):
        d = ObservationExtractionDiagnostics(question_index=0, session_id="s")
        assert d.rule_diagnostics == ()


class TestObservationExtractionDiagnosticsImmutability:
    def test_frozen(self):
        d = ObservationExtractionDiagnostics(question_index=0, session_id="s")
        with pytest.raises(ValidationError):
            d.rules_evaluated = 5

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationExtractionDiagnostics(
                question_index=0, session_id="s", extra="x"  # type: ignore[call-arg]
            )


class TestObservationExtractionDiagnosticsFromRuleDiagnostics:
    def test_empty_diagnostics(self):
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(0, "s", [])
        assert d.rules_evaluated == 0
        assert d.rules_skipped == 0
        assert d.rules_errored == 0
        assert d.total_matches == 0
        assert d.rule_diagnostics == ()

    def test_one_evaluated_rule(self):
        rule_d = ObservationRuleDiagnostic(rule_id="r", evaluated=True, match_count=2)
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(0, "s", [rule_d])
        assert d.rules_evaluated == 1
        assert d.total_matches == 2

    def test_one_skipped_rule(self):
        rule_d = ObservationRuleDiagnostic(rule_id="r", evaluated=False, skipped=True)
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(0, "s", [rule_d])
        assert d.rules_skipped == 1
        assert d.rules_evaluated == 0

    def test_one_errored_rule(self):
        rule_d = ObservationRuleDiagnostic(rule_id="r", error_message="fail")
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(0, "s", [rule_d])
        assert d.rules_errored == 1

    def test_mixed_rules(self):
        # error_message rule: evaluated=True (default), error_message set
        # it counts as evaluated (evaluated=True, not skipped) AND errored
        diagnostics = [
            ObservationRuleDiagnostic(rule_id="e1", evaluated=True, match_count=3),
            ObservationRuleDiagnostic(rule_id="e2", evaluated=True, match_count=1),
            ObservationRuleDiagnostic(rule_id="s1", evaluated=False, skipped=True),
            ObservationRuleDiagnostic(rule_id="err1", evaluated=True, error_message="boom"),
        ]
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(5, "sess", diagnostics)
        assert d.question_index == 5
        assert d.session_id == "sess"
        assert d.rules_evaluated == 3  # e1, e2, err1 (all evaluated=True, not skipped)
        assert d.rules_skipped == 1
        assert d.rules_errored == 1
        assert d.total_matches == 4
        assert len(d.rule_diagnostics) == 4

    def test_session_id_stored(self):
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(0, "my-session", [])
        assert d.session_id == "my-session"

    def test_question_index_stored(self):
        d = ObservationExtractionDiagnostics.from_rule_diagnostics(7, "s", [])
        assert d.question_index == 7
