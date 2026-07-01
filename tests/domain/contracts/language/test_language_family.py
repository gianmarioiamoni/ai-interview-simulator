# tests/domain/contracts/language/test_language_family.py

import pytest
from domain.contracts.language.language_family import LanguageFamily


class TestLanguageFamily:
    def test_v12_active_families_exist(self):
        assert LanguageFamily.PYTHON == "python"
        assert LanguageFamily.JAVASCRIPT == "javascript"
        assert LanguageFamily.TYPESCRIPT == "typescript"

    def test_reserved_future_families_exist(self):
        assert LanguageFamily.JVM == "jvm"
        assert LanguageFamily.SYSTEMS == "systems"
        assert LanguageFamily.DOTNET == "dotnet"
        assert LanguageFamily.OTHER == "other"

    def test_str_values_match_enum_names_lowercase(self):
        assert LanguageFamily.PYTHON.value == "python"
        assert LanguageFamily.JAVASCRIPT.value == "javascript"
        assert LanguageFamily.TYPESCRIPT.value == "typescript"

    def test_is_str_enum(self):
        assert isinstance(LanguageFamily.PYTHON, str)

    def test_comparison_with_string(self):
        assert LanguageFamily.PYTHON == "python"
        assert LanguageFamily.JAVASCRIPT == "javascript"

    def test_all_families_unique(self):
        values = [f.value for f in LanguageFamily]
        assert len(values) == len(set(values))

    def test_membership(self):
        assert "python" in [f.value for f in LanguageFamily]
        assert "unknown_lang" not in [f.value for f in LanguageFamily]
