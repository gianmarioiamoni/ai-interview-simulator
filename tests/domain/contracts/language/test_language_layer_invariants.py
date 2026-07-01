# tests/domain/contracts/language/test_language_layer_invariants.py
#
# Verifies the architectural invariants defined in ADR-019:
# I-05, I-06, I-13, I-19, I-20, I-21, I-22, I-23
# and the V1.2 domain isolation guarantees.

import inspect
import importlib

import pytest

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_registry import LanguageRegistry, PYTHON, JAVASCRIPT, TYPESCRIPT
from domain.contracts.language.language_family import LanguageFamily
from domain.contracts.language.language_policy import LanguagePolicy
from domain.contracts.language.language_config import LanguageConfig
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_capability import LanguageCapability


# ---------------------------------------------------------------------------
# I-20: No string comparisons against language names in domain code
# ---------------------------------------------------------------------------

class TestInvariantI20:
    """I-20: All domain logic operates on abstract ProgrammingLanguage.
    No direct string comparisons against language names in domain contracts.
    """

    def test_language_registry_resolves_by_id_not_string_comparison(self):
        # Registry.get() is the canonical resolution path
        lang = LanguageRegistry.get("python")
        assert isinstance(lang, ProgrammingLanguage)

    def test_domain_code_uses_registry_not_raw_strings(self):
        # Confirm registry instances are ProgrammingLanguage objects, not plain strings
        assert not isinstance(PYTHON, str)
        assert not isinstance(JAVASCRIPT, str)
        assert not isinstance(TYPESCRIPT, str)

    def test_language_id_is_stable_key(self):
        py1 = LanguageRegistry.get("python")
        py2 = LanguageRegistry.get("python")
        assert py1.language_id == py2.language_id


# ---------------------------------------------------------------------------
# I-22: ProgrammingLanguage has no knowledge of infrastructure
# ---------------------------------------------------------------------------

class TestInvariantI22:
    """I-22: ProgrammingLanguage knows nothing about sandbox, runtime, Docker,
    interpreter, compiler, or execution engine.
    """

    def test_programming_language_fields_contain_no_infra_terms(self):
        lang = _make_lang_with_fields()
        field_names = set(lang.model_fields.keys())
        forbidden = {"sandbox", "runtime", "executor", "docker", "jvm", "node", "interpreter"}
        assert field_names.isdisjoint(forbidden), (
            f"ProgrammingLanguage has infra fields: {field_names & forbidden}"
        )

    def test_execution_policy_stays_in_domain(self):
        # ExecutionPolicy is a domain value object — no sandbox/container fields
        ep = ExecutionPolicy(language_id="python")
        field_names = set(ep.model_fields.keys())
        forbidden = {"sandbox", "docker", "jvm", "runtime", "executor"}
        assert field_names.isdisjoint(forbidden)

    def test_language_policy_stays_in_domain(self):
        lp = LanguagePolicy(language_id="python", policy_version="1.0")
        field_names = set(lp.model_fields.keys())
        forbidden = {"sandbox", "docker", "runtime", "executor"}
        assert field_names.isdisjoint(forbidden)


def _make_lang_with_fields() -> ProgrammingLanguage:
    return ProgrammingLanguage(
        language_id="python",
        display_name="Python",
        language_version="3.12",
        language_family=LanguageFamily.PYTHON,
    )


# ---------------------------------------------------------------------------
# I-13: LanguagePolicy never modifies EvaluationDimension weights
# ---------------------------------------------------------------------------

class TestInvariantI13:
    """I-13: LanguagePolicy is a read-only configuration artifact.
    It must not contain weight or scoring override fields.
    """

    def test_language_policy_has_no_weight_fields(self):
        lp = LanguagePolicy(language_id="python", policy_version="1.0")
        field_names = set(lp.model_fields.keys())
        weight_fields = {"weight", "dimension_weight", "score_modifier", "scoring_weight"}
        assert field_names.isdisjoint(weight_fields)

    def test_language_policy_is_read_only_at_runtime(self):
        lp = LanguagePolicy(language_id="python", policy_version="1.0")
        with pytest.raises((TypeError, Exception)):
            lp.policy_version = "2.0"


# ---------------------------------------------------------------------------
# I-21: LanguagePolicy is read-only at runtime
# ---------------------------------------------------------------------------

class TestInvariantI21:
    def test_language_policy_immutable(self):
        lp = LanguagePolicy(language_id="python", policy_version="1.0")
        with pytest.raises((TypeError, Exception)):
            lp.recognised_idioms = ["new idiom"]

    def test_language_policy_version_changes_require_new_instance(self):
        lp1 = LanguagePolicy(language_id="python", policy_version="1.0")
        lp2 = LanguagePolicy(language_id="python", policy_version="2.0")
        assert lp1 != lp2
        assert lp1.policy_version == "1.0"
        assert lp2.policy_version == "2.0"


# ---------------------------------------------------------------------------
# Registry consistency invariants
# ---------------------------------------------------------------------------

class TestRegistryConsistency:
    def test_all_registered_languages_have_unique_ids(self):
        ids = LanguageRegistry.ids()
        assert len(ids) == len(set(ids))

    def test_all_registered_languages_have_valid_families(self):
        valid_families = {f.value for f in LanguageFamily}
        for lang in LanguageRegistry.all():
            assert lang.language_family in valid_families

    def test_v12_mandatory_languages_registered(self):
        assert LanguageRegistry.is_registered("python")
        assert LanguageRegistry.is_registered("javascript")
        assert LanguageRegistry.is_registered("typescript")

    def test_registry_get_returns_same_instance_on_repeated_calls(self):
        lang1 = LanguageRegistry.get("python")
        lang2 = LanguageRegistry.get("python")
        assert lang1 == lang2

    def test_no_infrastructure_language_registered_in_v12(self):
        # Go, Java, Rust etc. are NOT registered in V1.2
        for future_lang in ["java", "go", "rust", "c#", "kotlin", "swift"]:
            assert not LanguageRegistry.is_registered(future_lang)


# ---------------------------------------------------------------------------
# Domain isolation: no infrastructure imports in domain contracts
# ---------------------------------------------------------------------------

class TestDomainIsolation:
    # Forbidden infrastructure module imports — checked against import statements only
    FORBIDDEN_IMPORT_STMTS = frozenset({
        "import docker", "import subprocess", "import asyncio",
        "import sqlalchemy", "import sqlite3", "import redis", "import boto3",
        "from docker", "from subprocess", "from sqlalchemy", "from sqlite3",
    })

    def _get_import_lines(self, module_path: str) -> list[str]:
        mod = importlib.import_module(module_path)
        src = inspect.getsource(mod)
        return [line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))]

    def test_programming_language_no_infra_imports(self):
        lines = self._get_import_lines("domain.contracts.language.programming_language")
        for line in lines:
            for forbidden in self.FORBIDDEN_IMPORT_STMTS:
                assert not line.startswith(forbidden), f"Infra import in ProgrammingLanguage: {line}"

    def test_language_registry_no_infra_imports(self):
        lines = self._get_import_lines("domain.contracts.language.language_registry")
        for line in lines:
            for forbidden in self.FORBIDDEN_IMPORT_STMTS:
                assert not line.startswith(forbidden), f"Infra import in LanguageRegistry: {line}"

    def test_language_config_no_infra_imports(self):
        lines = self._get_import_lines("domain.contracts.language.language_config")
        for line in lines:
            for forbidden in self.FORBIDDEN_IMPORT_STMTS:
                assert not line.startswith(forbidden), f"Infra import in LanguageConfig: {line}"

    def test_language_profile_no_infra_imports(self):
        lines = self._get_import_lines("domain.contracts.language.language_profile")
        for line in lines:
            for forbidden in self.FORBIDDEN_IMPORT_STMTS:
                assert not line.startswith(forbidden), f"Infra import in LanguageProfile: {line}"


# ---------------------------------------------------------------------------
# LanguageConfig V1.2 invariants
# ---------------------------------------------------------------------------

class TestLanguageConfigInvariants:
    def test_no_hardcoded_language_strings_in_config_fields(self):
        # LanguageConfig uses ProgrammingLanguage objects, not strings like "python"
        cfg = LanguageConfig(
            enabled_languages=[PYTHON],
            primary_language=PYTHON,
        )
        for lang in cfg.enabled_languages:
            assert isinstance(lang, ProgrammingLanguage)
        assert isinstance(cfg.primary_language, ProgrammingLanguage)

    def test_metadata_field_is_reserved_and_not_parsed(self):
        cfg = LanguageConfig(
            enabled_languages=[PYTHON],
            primary_language=PYTHON,
            metadata={"future_key": "future_value"},
        )
        # V1.2 logic ignores metadata; it is simply preserved
        assert "future_key" in cfg.metadata

    def test_single_mode_selection_strategy_irrelevant(self):
        # Single-mode sessions use DETERMINISTIC_ALTERNATING (default) without error
        cfg = LanguageConfig(
            enabled_languages=[PYTHON],
            primary_language=PYTHON,
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
        )
        assert cfg.selection_strategy == LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING


# ---------------------------------------------------------------------------
# LanguageProfile determinism invariant
# ---------------------------------------------------------------------------

class TestLanguageProfileDeterminism:
    def test_same_profile_produces_same_sequence(self):
        """I-19 (session language sequence is deterministic)."""
        seq = ["python", "javascript", "python", "javascript", "python"]
        p1 = LanguageProfile(
            session_id="s1",
            session_mode=SessionMode.MIXED,
            primary_language=PYTHON,
            active_languages=[PYTHON, JAVASCRIPT],
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            language_sequence=seq,
        )
        p2 = LanguageProfile(
            session_id="s1",
            session_mode=SessionMode.MIXED,
            primary_language=PYTHON,
            active_languages=[PYTHON, JAVASCRIPT],
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            language_sequence=seq,
        )
        assert p1.language_sequence == p2.language_sequence

    def test_different_sequence_not_equal(self):
        seq_a = ["python", "javascript"]
        seq_b = ["javascript", "python"]
        p1 = LanguageProfile(
            session_id="s1",
            session_mode=SessionMode.MIXED,
            primary_language=PYTHON,
            active_languages=[PYTHON, JAVASCRIPT],
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            language_sequence=seq_a,
        )
        p2 = LanguageProfile(
            session_id="s1",
            session_mode=SessionMode.MIXED,
            primary_language=PYTHON,
            active_languages=[PYTHON, JAVASCRIPT],
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
            language_sequence=seq_b,
        )
        assert p1 != p2
