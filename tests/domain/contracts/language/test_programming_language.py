# tests/domain/contracts/language/test_programming_language.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_family import LanguageFamily


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_lang(**overrides) -> ProgrammingLanguage:
    defaults = dict(
        language_id="python",
        display_name="Python",
        language_version="3.12",
        language_family=LanguageFamily.PYTHON,
    )
    defaults.update(overrides)
    return ProgrammingLanguage(**defaults)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestProgrammingLanguageConstruction:
    def test_valid_python(self):
        lang = _make_lang()
        assert lang.language_id == "python"
        assert lang.display_name == "Python"
        assert lang.language_version == "3.12"
        assert lang.language_family == LanguageFamily.PYTHON

    def test_valid_javascript(self):
        lang = _make_lang(
            language_id="javascript",
            display_name="JavaScript",
            language_version="22",
            language_family=LanguageFamily.JAVASCRIPT,
        )
        assert lang.language_id == "javascript"

    def test_valid_typescript(self):
        lang = _make_lang(
            language_id="typescript",
            display_name="TypeScript",
            language_version="5.4",
            language_family=LanguageFamily.TYPESCRIPT,
        )
        assert lang.language_id == "typescript"

    def test_future_language_jvm(self):
        lang = _make_lang(
            language_id="java",
            display_name="Java",
            language_version="21",
            language_family=LanguageFamily.JVM,
        )
        assert lang.language_family == LanguageFamily.JVM

    def test_schema_version_default(self):
        lang = _make_lang()
        assert lang.schema_version == "1.0"

    def test_schema_version_explicit(self):
        lang = _make_lang(schema_version="2.0")
        assert lang.schema_version == "2.0"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestProgrammingLanguageValidation:
    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            _make_lang(language_id="")

    def test_empty_display_name_rejected(self):
        with pytest.raises(ValidationError):
            _make_lang(display_name="")

    def test_empty_language_version_rejected(self):
        with pytest.raises(ValidationError):
            _make_lang(language_version="")

    def test_empty_language_family_rejected(self):
        with pytest.raises(ValidationError):
            _make_lang(language_family="")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_lang(unknown_field="x")


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

class TestProgrammingLanguageImmutability:
    def test_language_id_frozen(self):
        lang = _make_lang()
        with pytest.raises((ValidationError, TypeError)):
            lang.language_id = "javascript"

    def test_display_name_frozen(self):
        lang = _make_lang()
        with pytest.raises((ValidationError, TypeError)):
            lang.display_name = "Other"

    def test_language_version_frozen(self):
        lang = _make_lang()
        with pytest.raises((ValidationError, TypeError)):
            lang.language_version = "3.13"

    def test_language_family_frozen(self):
        lang = _make_lang()
        with pytest.raises((ValidationError, TypeError)):
            lang.language_family = LanguageFamily.JAVASCRIPT


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

class TestProgrammingLanguageSerialization:
    def test_roundtrip(self):
        lang = _make_lang()
        data = lang.model_dump()
        lang2 = ProgrammingLanguage(**data)
        assert lang == lang2

    def test_model_dump_contains_expected_keys(self):
        lang = _make_lang()
        data = lang.model_dump()
        assert "language_id" in data
        assert "display_name" in data
        assert "language_version" in data
        assert "language_family" in data
        assert "schema_version" in data

    def test_json_roundtrip(self):
        lang = _make_lang()
        json_str = lang.model_dump_json()
        lang2 = ProgrammingLanguage.model_validate_json(json_str)
        assert lang == lang2


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------

class TestProgrammingLanguageEquality:
    def test_equal_instances(self):
        lang1 = _make_lang()
        lang2 = _make_lang()
        assert lang1 == lang2

    def test_different_language_id_not_equal(self):
        lang1 = _make_lang(language_id="python")
        lang2 = _make_lang(
            language_id="javascript",
            display_name="JavaScript",
            language_version="22",
            language_family=LanguageFamily.JAVASCRIPT,
        )
        assert lang1 != lang2

    def test_different_version_not_equal(self):
        lang1 = _make_lang(language_version="3.12")
        lang2 = _make_lang(language_version="3.13")
        assert lang1 != lang2
