# tests/domain/contracts/language/test_language_policy.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.language_policy import LanguagePolicy


def _make_policy(**overrides) -> LanguagePolicy:
    defaults = dict(language_id="python", policy_version="1.0")
    defaults.update(overrides)
    return LanguagePolicy(**defaults)


class TestLanguagePolicyConstruction:
    def test_minimal(self):
        p = _make_policy()
        assert p.language_id == "python"
        assert p.policy_version == "1.0"
        assert p.recognised_idioms == []
        assert p.type_error_patterns == []
        assert p.import_allowlist == []
        assert p.import_blocklist == []
        assert p.schema_version == "1.0"

    def test_with_idioms(self):
        p = _make_policy(recognised_idioms=["list comprehension", "generator expression"])
        assert "list comprehension" in p.recognised_idioms

    def test_with_type_errors(self):
        p = _make_policy(type_error_patterns=["TypeError", "AttributeError"])
        assert "TypeError" in p.type_error_patterns

    def test_with_allowlist(self):
        p = _make_policy(import_allowlist=["math", "collections", "itertools"])
        assert "math" in p.import_allowlist

    def test_with_blocklist(self):
        p = _make_policy(import_blocklist=["os", "subprocess", "socket"])
        assert "os" in p.import_blocklist

    def test_javascript_policy(self):
        p = _make_policy(
            language_id="javascript",
            policy_version="1.0",
            recognised_idioms=["arrow function", "destructuring", "async/await"],
        )
        assert p.language_id == "javascript"


class TestLanguagePolicyValidation:
    def test_empty_language_id_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(language_id="")

    def test_empty_policy_version_rejected(self):
        with pytest.raises(ValidationError):
            _make_policy(policy_version="")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_policy(unknown_field="x")


class TestLanguagePolicyImmutability:
    def test_language_id_frozen(self):
        p = _make_policy()
        with pytest.raises((ValidationError, TypeError)):
            p.language_id = "javascript"

    def test_policy_version_frozen(self):
        p = _make_policy()
        with pytest.raises((ValidationError, TypeError)):
            p.policy_version = "2.0"

    def test_model_itself_frozen(self):
        p = _make_policy(recognised_idioms=["list comprehension"])
        with pytest.raises((ValidationError, TypeError)):
            p.recognised_idioms = ["generator"]


class TestLanguagePolicySerialization:
    def test_roundtrip(self):
        p = _make_policy(
            recognised_idioms=["list comprehension"],
            import_allowlist=["math"],
            import_blocklist=["os"],
        )
        data = p.model_dump()
        p2 = LanguagePolicy(**data)
        assert p == p2

    def test_json_roundtrip(self):
        p = _make_policy(type_error_patterns=["TypeError"])
        json_str = p.model_dump_json()
        p2 = LanguagePolicy.model_validate_json(json_str)
        assert p == p2


class TestLanguagePolicyVersioning:
    def test_different_versions_not_equal(self):
        p1 = _make_policy(policy_version="1.0")
        p2 = _make_policy(policy_version="2.0")
        assert p1 != p2

    def test_same_version_equal(self):
        p1 = _make_policy(policy_version="1.0")
        p2 = _make_policy(policy_version="1.0")
        assert p1 == p2
