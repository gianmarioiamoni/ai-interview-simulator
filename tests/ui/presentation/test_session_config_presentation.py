# tests/ui/presentation/test_session_config_presentation.py
# EPIC-07 P3/C5 — SessionConfigPresentation + DM-V-SC-01/02/03.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ui.presentation import (
    SessionConfigPresentation,
    derive_language_mode,
    is_language_mode_complete,
    validate_language_mode_coupling,
    validate_language_mode_not_locale_alone,
)


class TestDeriveLanguageMode:
    def test_single(self) -> None:
        assert derive_language_mode(("python",)) == "single"

    def test_mixed(self) -> None:
        assert derive_language_mode(("python", "javascript")) == "mixed"


class TestDmVScCoupling:
    def test_dm_v_sc_01_mixed_requires_multiple(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SC-01"):
            validate_language_mode_coupling("mixed", ("python",))

    def test_dm_v_sc_02_single_requires_one(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SC-02"):
            validate_language_mode_coupling("single", ("python", "javascript"))

    def test_valid_couplings(self) -> None:
        validate_language_mode_coupling("single", ("python",))
        validate_language_mode_coupling("mixed", ("python", "typescript"))


class TestDmVSc03LocaleAloneInsufficient:
    def test_locale_alone_rejected(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SC-03"):
            validate_language_mode_not_locale_alone(None, "en")
        with pytest.raises(ValueError, match="DM-V-SC-03"):
            validate_language_mode_not_locale_alone((), "it")

    def test_locale_alone_not_complete(self) -> None:
        assert is_language_mode_complete(None, "en") is False
        assert is_language_mode_complete([], "en") is False

    def test_enabled_languages_complete_without_locale(self) -> None:
        assert is_language_mode_complete(("python",), None) is True
        assert is_language_mode_complete(("python", "javascript"), "en") is True


class TestSessionConfigPresentation:
    def test_from_setup_inputs_derives_single_mode(self) -> None:
        config = SessionConfigPresentation.from_setup_inputs(
            role="backend_engineer",
            seniority="mid",
            enabled_languages=["python"],
            interview_type="TECHNICAL",
            interview_length=20,
            ui_locale="en",
            company="Acme",
        )
        assert config.language_mode == "single"
        assert config.enabled_languages == ("python",)
        assert config.ui_locale == "en"

    def test_from_setup_inputs_derives_mixed_mode(self) -> None:
        config = SessionConfigPresentation.from_setup_inputs(
            role="backend_engineer",
            seniority="senior",
            enabled_languages=["python", "javascript"],
            interview_type="TECHNICAL",
            interview_length="20",
            ui_locale="it",
        )
        assert config.language_mode == "mixed"

    def test_locale_alone_cannot_build(self) -> None:
        with pytest.raises(ValueError, match="DM-V-SC-03"):
            SessionConfigPresentation.from_setup_inputs(
                role="backend_engineer",
                seniority="mid",
                enabled_languages=[],
                interview_type="TECHNICAL",
                interview_length=20,
                ui_locale="en",
            )

    def test_mismatched_mode_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SessionConfigPresentation(
                role="backend_engineer",
                seniority="mid",
                language_mode="single",
                enabled_languages=("python", "javascript"),
                interview_type="TECHNICAL",
                interview_length="20",
            )

    def test_unsupported_combination_rejected(self) -> None:
        with pytest.raises(ValueError, match="ADR-019"):
            SessionConfigPresentation.from_setup_inputs(
                role="backend_engineer",
                seniority="mid",
                enabled_languages=["javascript", "typescript"],
                interview_type="TECHNICAL",
                interview_length=20,
            )

    def test_immutable_and_extra_forbid(self) -> None:
        config = SessionConfigPresentation.from_setup_inputs(
            role="backend_engineer",
            seniority="mid",
            enabled_languages=["typescript"],
            interview_type="TECHNICAL",
            interview_length=20,
        )
        with pytest.raises(ValidationError):
            config.language_mode = "mixed"  # type: ignore[misc]
        with pytest.raises(ValidationError):
            SessionConfigPresentation(
                role="backend_engineer",
                seniority="mid",
                language_mode="single",
                enabled_languages=("python",),
                interview_type="TECHNICAL",
                interview_length="20",
                session_mode="single",  # type: ignore[call-arg]
            )
