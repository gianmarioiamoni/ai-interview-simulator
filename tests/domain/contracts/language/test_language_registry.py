# tests/domain/contracts/language/test_language_registry.py

import pytest
from domain.contracts.language.language_registry import LanguageRegistry, PYTHON, JAVASCRIPT, TYPESCRIPT
from domain.contracts.language.language_family import LanguageFamily
from domain.contracts.language.programming_language import ProgrammingLanguage


class TestLanguageRegistryConstants:
    def test_python_constant(self):
        assert PYTHON.language_id == "python"
        assert PYTHON.language_family == LanguageFamily.PYTHON

    def test_javascript_constant(self):
        assert JAVASCRIPT.language_id == "javascript"
        assert JAVASCRIPT.language_family == LanguageFamily.JAVASCRIPT

    def test_typescript_constant(self):
        assert TYPESCRIPT.language_id == "typescript"
        assert TYPESCRIPT.language_family == LanguageFamily.TYPESCRIPT

    def test_constants_are_frozen(self):
        with pytest.raises((TypeError, Exception)):
            PYTHON.language_id = "other"

    def test_constants_are_programming_language_instances(self):
        assert isinstance(PYTHON, ProgrammingLanguage)
        assert isinstance(JAVASCRIPT, ProgrammingLanguage)
        assert isinstance(TYPESCRIPT, ProgrammingLanguage)


class TestLanguageRegistryGet:
    def test_get_python(self):
        lang = LanguageRegistry.get("python")
        assert lang == PYTHON

    def test_get_javascript(self):
        lang = LanguageRegistry.get("javascript")
        assert lang == JAVASCRIPT

    def test_get_typescript(self):
        lang = LanguageRegistry.get("typescript")
        assert lang == TYPESCRIPT

    def test_get_unregistered_raises_key_error(self):
        with pytest.raises(KeyError):
            LanguageRegistry.get("java")

    def test_get_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            LanguageRegistry.get("")

    def test_get_case_sensitive(self):
        with pytest.raises(KeyError):
            LanguageRegistry.get("Python")

    def test_get_returns_same_instance(self):
        lang1 = LanguageRegistry.get("python")
        lang2 = LanguageRegistry.get("python")
        assert lang1 == lang2


class TestLanguageRegistryAll:
    def test_all_returns_list(self):
        result = LanguageRegistry.all()
        assert isinstance(result, list)

    def test_all_contains_v12_languages(self):
        result = LanguageRegistry.all()
        ids = [lang.language_id for lang in result]
        assert "python" in ids
        assert "javascript" in ids
        assert "typescript" in ids

    def test_all_returns_at_least_three(self):
        assert len(LanguageRegistry.all()) >= 3

    def test_all_returns_programming_language_instances(self):
        for lang in LanguageRegistry.all():
            assert isinstance(lang, ProgrammingLanguage)


class TestLanguageRegistryIds:
    def test_ids_returns_list_of_strings(self):
        ids = LanguageRegistry.ids()
        assert isinstance(ids, list)
        assert all(isinstance(i, str) for i in ids)

    def test_ids_contains_v12_ids(self):
        ids = LanguageRegistry.ids()
        assert "python" in ids
        assert "javascript" in ids
        assert "typescript" in ids


class TestLanguageRegistryIsRegistered:
    def test_python_is_registered(self):
        assert LanguageRegistry.is_registered("python") is True

    def test_javascript_is_registered(self):
        assert LanguageRegistry.is_registered("javascript") is True

    def test_typescript_is_registered(self):
        assert LanguageRegistry.is_registered("typescript") is True

    def test_java_not_registered(self):
        assert LanguageRegistry.is_registered("java") is False

    def test_empty_string_not_registered(self):
        assert LanguageRegistry.is_registered("") is False


class TestLanguageRegistryByFamily:
    def test_python_family_returns_python(self):
        result = LanguageRegistry.by_family(LanguageFamily.PYTHON)
        assert len(result) == 1
        assert result[0].language_id == "python"

    def test_javascript_family_returns_javascript(self):
        result = LanguageRegistry.by_family(LanguageFamily.JAVASCRIPT)
        assert len(result) == 1
        assert result[0].language_id == "javascript"

    def test_jvm_family_returns_empty_in_v12(self):
        result = LanguageRegistry.by_family(LanguageFamily.JVM)
        assert result == []

    def test_systems_family_returns_empty_in_v12(self):
        result = LanguageRegistry.by_family(LanguageFamily.SYSTEMS)
        assert result == []


class TestLanguageRegistryInvariants:
    def test_no_duplicate_ids(self):
        ids = LanguageRegistry.ids()
        assert len(ids) == len(set(ids))

    def test_all_and_get_consistent(self):
        for lang in LanguageRegistry.all():
            assert LanguageRegistry.get(lang.language_id) == lang
