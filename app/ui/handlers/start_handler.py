# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview


def start_handler(role, interview_type, company, language):

    response = start_interview(
        role=role,
        interview_type=interview_type,
        company=company,
        language=language,
    )

    return response.to_gradio_outputs()
