# app/ui/presentation/session_config_presentation.py
# EPIC-07 EC-SC-01 / Data Model §4.4 — SessionConfigPresentation (UI-layer; ephemeral).

from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel, Field, field_validator, model_validator

from app.ui.presentation.session_config_validation import (
    LanguageMode,
    derive_language_mode,
    validate_enabled_languages_vocabulary,
    validate_language_mode_coupling,
    validate_language_mode_not_locale_alone,
)

UiLocale = Literal["en", "it"]


class SessionConfigPresentation(BaseModel):
    """Immutable candidate-facing session configuration intent (EC-SC-01)."""

    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    language_mode: LanguageMode
    enabled_languages: tuple[str, ...] = Field(..., min_length=1)
    interview_type: str = Field(..., min_length=1)
    interview_length: str = Field(..., min_length=1)
    ui_locale: UiLocale | None = None
    company: str | None = None

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_setup_inputs(
        cls,
        *,
        role: str,
        seniority: str,
        enabled_languages: Sequence[str],
        interview_type: str,
        interview_length: str | int,
        ui_locale: str | None = None,
        company: str | None = None,
    ) -> SessionConfigPresentation:
        """Build from setup widgets; derive language_mode from enabled_languages."""
        languages = tuple(enabled_languages)
        validate_language_mode_not_locale_alone(languages, ui_locale)
        validate_enabled_languages_vocabulary(languages)
        mode = derive_language_mode(languages)
        locale: UiLocale | None
        if ui_locale is None or str(ui_locale).strip() == "":
            locale = None
        else:
            locale = ui_locale  # type: ignore[assignment]
        return cls(
            role=role,
            seniority=seniority,
            language_mode=mode,
            enabled_languages=languages,
            interview_type=interview_type,
            interview_length=str(interview_length),
            ui_locale=locale,
            company=company if company and str(company).strip() else None,
        )

    @field_validator("ui_locale")
    @classmethod
    def _validate_ui_locale(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in ("en", "it"):
            raise ValueError("ui_locale must be 'en', 'it', or null.")
        return value

    @model_validator(mode="after")
    def _validate_dm_v_sc(self) -> SessionConfigPresentation:
        validate_enabled_languages_vocabulary(self.enabled_languages)
        validate_language_mode_coupling(self.language_mode, self.enabled_languages)
        validate_language_mode_not_locale_alone(self.enabled_languages, self.ui_locale)
        return self
