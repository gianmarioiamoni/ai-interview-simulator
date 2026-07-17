# app/ui/presentation/session_config_validation.py
# EPIC-07 Data Model §4.4 — DM-V-SC validation helpers (ADR-019 language mode).

from __future__ import annotations

from typing import Literal, Sequence

LanguageMode = Literal["single", "mixed"]

# ADR-019 Section E — V1.2 supported enabled_languages combinations.
_ALLOWED_ENABLED_LANGUAGE_SETS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"python"}),
        frozenset({"javascript"}),
        frozenset({"typescript"}),
        frozenset({"python", "javascript"}),
        frozenset({"python", "typescript"}),
    }
)


def derive_language_mode(enabled_languages: Sequence[str]) -> LanguageMode:
    """Derive ADR-019 session mode from enabled language ids."""
    count = len(enabled_languages)
    if count == 1:
        return "single"
    if count > 1:
        return "mixed"
    raise ValueError("DM-V-SC: enabled_languages must contain at least one language id.")


def validate_language_mode_coupling(
    language_mode: LanguageMode,
    enabled_languages: Sequence[str],
) -> None:
    """DM-V-SC-01 / DM-V-SC-02: mode ↔ enabled_languages length."""
    count = len(enabled_languages)
    if language_mode == "mixed" and count <= 1:
        raise ValueError(
            "DM-V-SC-01: language_mode='mixed' requires len(enabled_languages) > 1."
        )
    if language_mode == "single" and count != 1:
        raise ValueError(
            "DM-V-SC-02: language_mode='single' requires len(enabled_languages) == 1."
        )


def validate_enabled_languages_vocabulary(enabled_languages: Sequence[str]) -> None:
    """Fail-fast when enabled language ids are empty, duplicate, or outside ADR-019."""
    if not enabled_languages:
        raise ValueError("enabled_languages must be non-empty.")
    if len(set(enabled_languages)) != len(enabled_languages):
        raise ValueError("enabled_languages must not contain duplicates.")
    key = frozenset(enabled_languages)
    if key not in _ALLOWED_ENABLED_LANGUAGE_SETS:
        raise ValueError(
            f"enabled_languages={tuple(enabled_languages)!r} is not an ADR-019 "
            "supported combination."
        )


def validate_language_mode_not_locale_alone(
    enabled_languages: Sequence[str] | None,
    ui_locale: str | None,
) -> None:
    """DM-V-SC-03: ui_locale alone never satisfies language-mode completeness."""
    has_locale = ui_locale is not None and str(ui_locale).strip() != ""
    has_languages = bool(enabled_languages)
    if has_locale and not has_languages:
        raise ValueError(
            "DM-V-SC-03: ui_locale alone never satisfies language-mode completeness."
        )
    if not has_languages:
        raise ValueError(
            "DM-V-SC-03: enabled_languages required for language-mode completeness."
        )


def is_language_mode_complete(
    enabled_languages: Sequence[str] | None,
    ui_locale: str | None = None,
) -> bool:
    """Return True when language mode is complete (not locale-only)."""
    try:
        validate_language_mode_not_locale_alone(enabled_languages, ui_locale)
        languages = tuple(enabled_languages or ())
        validate_enabled_languages_vocabulary(languages)
        mode = derive_language_mode(languages)
        validate_language_mode_coupling(mode, languages)
        return True
    except ValueError:
        return False
