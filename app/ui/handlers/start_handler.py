# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview
from domain.contracts.interview_type import InterviewType
from domain.contracts.role import RoleType


def start_handler(role: RoleType, interview_type: InterviewType, company: str, language: str):

    response = start_interview(
        role=role,
        interview_type=interview_type,
        company=company,
        language=language,
    )

    return response.to_gradio_outputs()
