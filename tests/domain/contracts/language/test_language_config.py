# tests/domain/contracts/language/test_language_config.py

import pytest
from pydantic import ValidationError

from domain.contracts.language.language_config import LanguageConfig
from domain.contracts.language.language_registry import PYTHON, JAVASCRIPT, TYPESCRIPT
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_single_config(**overrides) -> LanguageConfig:
    defaults = dict(
        enabled_languages=[PYTHON],
        primary_language=PYTHON,
    )
    defaults.update(overrides)
    return LanguageConfig(**defaults)


def _make_mixed_config(**overrides) -> LanguageConfig:
    defaults = dict(
        enabled_languages=[PYTHON, JAVASCRIPT],
        primary_language=PYTHON,
    )
    defaults.update(overrides)
    return LanguageConfig(**defaults)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestLanguageConfigConstruction:
    def test_python_only(self):
        cfg = _make_single_config()
        assert len(cfg.enabled_languages) == 1
        assert cfg.primary_language.language_id == "python"
        assert cfg.mixed_mode is False
        assert cfg.schema_version == "1.0"

    def test_javascript_only(self):
        cfg = LanguageConfig(
            enabled_languages=[JAVASCRIPT],
            primary_language=JAVASCRIPT,
        )
        assert cfg.primary_language.language_id == "javascript"
        assert cfg.mixed_mode is False

    def test_typescript_only(self):
        cfg = LanguageConfig(
            enabled_languages=[TYPESCRIPT],
            primary_language=TYPESCRIPT,
        )
        assert cfg.primary_language.language_id == "typescript"

    def test_mixed_python_javascript(self):
        cfg = _make_mixed_config()
        assert cfg.mixed_mode is True
        assert len(cfg.enabled_languages) == 2

    def test_mixed_python_typescript(self):
        cfg = LanguageConfig(
            enabled_languages=[PYTHON, TYPESCRIPT],
            primary_language=PYTHON,
        )
        assert cfg.mixed_mode is True

    def test_default_strategy_is_deterministic(self):
        cfg = _make_single_config()
        assert cfg.selection_strategy == LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING

    def test_metadata_default_empty(self):
        cfg = _make_single_config()
        assert cfg.metadata == {}

    def test_metadata_is_reserved_and_ignored(self):
        cfg = _make_single_config(metadata={"experiment": "abc"})
        assert cfg.metadata["experiment"] == "abc"


# ---------------------------------------------------------------------------
# mixed_mode property
# ---------------------------------------------------------------------------

class TestLanguageConfigMixedMode:
    def test_single_mixed_mode_false(self):
        cfg = _make_single_config()
        assert cfg.mixed_mode is False

    def test_two_langs_mixed_mode_true(self):
        cfg = _make_mixed_config()
        assert cfg.mixed_mode is True

    def test_mixed_mode_is_derived_not_stored(self):
        cfg = _make_mixed_config()
        # mixed_mode is a @property, not a field
        assert "mixed_mode" not in cfg.model_fields


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestLanguageConfigValidation:
    def test_primary_not_in_enabled_rejected(self):
        with pytest.raises(ValidationError, match="primary_language"):
            LanguageConfig(
                enabled_languages=[PYTHON],
                primary_language=JAVASCRIPT,
            )

    def test_mixed_with_non_deterministic_rejected(self):
        with pytest.raises(ValidationError, match="DETERMINISTIC_ALTERNATING"):
            LanguageConfig(
                enabled_languages=[PYTHON, JAVASCRIPT],
                primary_language=PYTHON,
                selection_strategy=LanguageSelectionStrategy.WEIGHTED_RANDOM,
            )

    def test_empty_enabled_languages_rejected(self):
        with pytest.raises(ValidationError):
            LanguageConfig(
                enabled_languages=[],
                primary_language=PYTHON,
            )

    def test_three_languages_rejected(self):
        with pytest.raises(ValidationError):
            LanguageConfig(
                enabled_languages=[PYTHON, JAVASCRIPT, TYPESCRIPT],
                primary_language=PYTHON,
            )

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            _make_single_config(unknown_field="x")

    def test_execution_policy_for_unknown_language_rejected(self):
        ep = ExecutionPolicy(language_id="java")
        with pytest.raises(ValidationError, match="enabled_languages"):
            _make_single_config(execution_policies=[ep])

    def test_language_policy_for_unknown_language_rejected(self):
        lp = LanguagePolicy(language_id="java", policy_version="1.0")
        with pytest.raises(ValidationError, match="enabled_languages"):
            _make_single_config(evaluation_policies=[lp])


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

class TestLanguageConfigImmutability:
    def test_enabled_languages_frozen(self):
        cfg = _make_single_config()
        with pytest.raises((ValidationError, TypeError)):
            cfg.enabled_languages = [JAVASCRIPT]

    def test_primary_language_frozen(self):
        cfg = _make_single_config()
        with pytest.raises((ValidationError, TypeError)):
            cfg.primary_language = JAVASCRIPT


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

class TestLanguageConfigSerialization:
    def test_single_roundtrip(self):
        cfg = _make_single_config()
        data = cfg.model_dump()
        cfg2 = LanguageConfig(**data)
        assert cfg == cfg2

    def test_mixed_roundtrip(self):
        cfg = _make_mixed_config()
        data = cfg.model_dump()
        cfg2 = LanguageConfig(**data)
        assert cfg == cfg2

    def test_json_roundtrip_single(self):
        cfg = _make_single_config()
        json_str = cfg.model_dump_json()
        cfg2 = LanguageConfig.model_validate_json(json_str)
        assert cfg == cfg2

    def test_json_roundtrip_mixed(self):
        cfg = _make_mixed_config()
        json_str = cfg.model_dump_json()
        cfg2 = LanguageConfig.model_validate_json(json_str)
        assert cfg == cfg2

    def test_with_execution_policies_roundtrip(self):
        ep = ExecutionPolicy(language_id="python", timeout_ms=3000)
        cfg = _make_single_config(execution_policies=[ep])
        data = cfg.model_dump()
        cfg2 = LanguageConfig(**data)
        assert cfg == cfg2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestLanguageConfigEdgeCases:
    def test_single_non_primary_selection_strategy_allowed(self):
        # DETERMINISTIC_ALTERNATING is allowed for single mode (no constraint)
        cfg = _make_single_config(
            selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING
        )
        assert cfg.selection_strategy == LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING

    def test_typescript_as_primary_in_mixed(self):
        cfg = LanguageConfig(
            enabled_languages=[PYTHON, TYPESCRIPT],
            primary_language=TYPESCRIPT,
        )
        assert cfg.primary_language.language_id == "typescript"
