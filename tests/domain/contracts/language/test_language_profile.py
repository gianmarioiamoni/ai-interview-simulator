# tests/domain/contracts/language/test_language_profile.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_registry import PYTHON, JAVASCRIPT, TYPESCRIPT
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_single_profile(**overrides) -> LanguageProfile:
    defaults = dict(
        session_id="sess-001",
        session_mode=SessionMode.SINGLE,
        primary_language=PYTHON,
        active_languages=[PYTHON],
        selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
    )
    defaults.update(overrides)
    return LanguageProfile(**defaults)


def _make_mixed_profile(**overrides) -> LanguageProfile:
    defaults = dict(
        session_id="sess-002",
        session_mode=SessionMode.MIXED,
        primary_language=PYTHON,
        active_languages=[PYTHON, JAVASCRIPT],
        selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
    )
    defaults.update(overrides)
    return LanguageProfile(**defaults)


# ---------------------------------------------------------------------------
# Construction — single mode
# ---------------------------------------------------------------------------

class TestLanguageProfileSingleMode:
    def test_single_python(self):
        p = _make_single_profile()
        assert p.session_mode == SessionMode.SINGLE
        assert p.primary_language == PYTHON
        assert len(p.active_languages) == 1

    def test_single_javascript(self):
        p = _make_single_profile(
            primary_language=JAVASCRIPT,
            active_languages=[JAVASCRIPT],
        )
        assert p.primary_language.language_id == "javascript"

    def test_single_typescript(self):
        p = _make_single_profile(
            primary_language=TYPESCRIPT,
            active_languages=[TYPESCRIPT],
        )
        assert p.primary_language.language_id == "typescript"

    def test_schema_version_default(self):
        p = _make_single_profile()
        assert p.schema_version == "1.0"

    def test_empty_language_sequence_allowed(self):
        p = _make_single_profile(language_sequence=[])
        assert p.language_sequence == []

    def test_language_sequence_with_python(self):
        p = _make_single_profile(language_sequence=["python", "python", "python"])
        assert p.language_sequence == ["python", "python", "python"]


# ---------------------------------------------------------------------------
# Construction — mixed mode
# ---------------------------------------------------------------------------

class TestLanguageProfileMixedMode:
    def test_mixed_python_javascript(self):
        p = _make_mixed_profile()
        assert p.session_mode == SessionMode.MIXED
        assert len(p.active_languages) == 2

    def test_mixed_language_sequence(self):
        p = _make_mixed_profile(
            language_sequence=["python", "javascript", "python", "javascript"]
        )
        assert p.language_sequence[0] == "python"
        assert p.language_sequence[1] == "javascript"

    def test_mixed_with_execution_policies(self):
        ep_py = ExecutionPolicy(language_id="python", timeout_ms=5000)
        ep_js = ExecutionPolicy(language_id="javascript", timeout_ms=8000)
        p = _make_mixed_profile(execution_policies=[ep_py, ep_js])
        assert len(p.execution_policies) == 2


# ---------------------------------------------------------------------------
# Validation — invariants
# ---------------------------------------------------------------------------

class TestLanguageProfileValidation:
    def test_primary_not_in_active_rejected(self):
        with pytest.raises(ValidationError, match="primary_language"):
            LanguageProfile(
                session_id="s",
                session_mode=SessionMode.SINGLE,
                primary_language=JAVASCRIPT,
                active_languages=[PYTHON],
                selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            )

    def test_single_mode_with_two_languages_rejected(self):
        with pytest.raises(ValidationError, match="SINGLE"):
            LanguageProfile(
                session_id="s",
                session_mode=SessionMode.SINGLE,
                primary_language=PYTHON,
                active_languages=[PYTHON, JAVASCRIPT],
                selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            )

    def test_mixed_mode_with_one_language_rejected(self):
        with pytest.raises(ValidationError, match="MIXED"):
            LanguageProfile(
                session_id="s",
                session_mode=SessionMode.MIXED,
                primary_language=PYTHON,
                active_languages=[PYTHON],
                selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            )

    def test_language_sequence_invalid_entry_rejected(self):
        with pytest.raises(ValidationError, match="language_sequence"):
            _make_single_profile(language_sequence=["java"])

    def test_empty_session_id_rejected(self):
        with pytest.raises(ValidationError):
            _make_single_profile(session_id="")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_single_profile(unknown="x")


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

class TestLanguageProfileImmutability:
    def test_session_mode_frozen(self):
        p = _make_single_profile()
        with pytest.raises((ValidationError, TypeError)):
            p.session_mode = SessionMode.MIXED

    def test_primary_language_frozen(self):
        p = _make_single_profile()
        with pytest.raises((ValidationError, TypeError)):
            p.primary_language = JAVASCRIPT


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

class TestLanguageProfileSerialization:
    def test_single_roundtrip(self):
        p = _make_single_profile(language_sequence=["python", "python"])
        data = p.model_dump()
        p2 = LanguageProfile(**data)
        assert p == p2

    def test_mixed_roundtrip(self):
        p = _make_mixed_profile(
            language_sequence=["python", "javascript", "python"]
        )
        data = p.model_dump()
        p2 = LanguageProfile(**data)
        assert p == p2

    def test_json_roundtrip_single(self):
        p = _make_single_profile()
        json_str = p.model_dump_json()
        p2 = LanguageProfile.model_validate_json(json_str)
        assert p == p2
