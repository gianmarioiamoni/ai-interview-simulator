# app/ui/handlers/start_handler.py
# EPIC-07 C5 — validate SessionConfigPresentation language mode before start.

from __future__ import annotations

from collections.abc import Sequence

from app.ui.presentation.session_config_presentation import SessionConfigPresentation
from app.ui.state_handlers import start_interview


def start_handler(
    role,
    role_custom_name,
    interview_type,
    seniority,
    interview_length,
    company,
    language,
    enabled_languages: Sequence[str] | None = None,
    job_description=None,
    company_description=None,
):
    # Intent-only presentation validation (AR-03: no new InterviewState fields).
    SessionConfigPresentation.from_setup_inputs(
        role=str(role),
        seniority=str(seniority),
        enabled_languages=tuple(enabled_languages or ()),
        interview_type=str(interview_type),
        interview_length=interview_length,
        ui_locale=language,
        company=company,
    )

    return start_interview(
        role=role,
        role_custom_name=role_custom_name,
        interview_type=interview_type,
        seniority=seniority,
        interview_length=int(interview_length),
        company=company,
        language=language,
        job_description=job_description,
        company_description=company_description,
    )
