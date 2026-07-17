# app/ui/bindings/validators/input_validator.py
# EPIC-07 C5 — start enablement requires language mode (not UI locale alone).

from __future__ import annotations

from typing import Sequence

import gradio as gr

from app.ui.presentation.session_config_validation import is_language_mode_complete


class InputValidator:
    def validate(
        self,
        role,
        role_custom_name,
        interview_type,
        seniority,
        interview_length,
        company,
        language,
        enabled_languages: Sequence[str] | None = None,
    ):
        role_valid = role is not None
        if role == "other":
            role_valid = bool(role_custom_name and role_custom_name.strip())

        language_mode_valid = is_language_mode_complete(
            enabled_languages,
            ui_locale=language,
        )

        valid = (
            role_valid
            and interview_type is not None
            and seniority is not None
            and interview_length is not None
            and company is not None
            and company.strip() != ""
            and language is not None
            and language_mode_valid
        )
        return gr.update(interactive=valid)
