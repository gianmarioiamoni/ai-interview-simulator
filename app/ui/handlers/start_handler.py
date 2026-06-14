# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview


def start_handler(role, role_custom_name, interview_type, seniority, interview_length, company, language):
    return start_interview(
        role=role,
        role_custom_name=role_custom_name,
        interview_type=interview_type,
        seniority=seniority,
        interview_length=int(interview_length),
        company=company,
        language=language,
    )
