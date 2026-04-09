# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType


def start_handler(role, interview_type, company, language):

    # STEP 1 → immediate loader
    yield (
        None,
        "",
        "⏳ Generating interview...",
        "", "", "",
        False, False, False,
        False, True, False, False,
        "",
        "",
        False, False, False,
        "", "", "",
    )

    # STEP 2 → real logic
    response = start_interview(
        role=role,
        interview_type=interview_type,
        company=company,
        language=language,
    )

    yield response.to_gradio_outputs()
