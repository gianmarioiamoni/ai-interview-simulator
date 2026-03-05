# app/ui/handlers/start_handler.py

from app.ui.state_handlers import start_interview


def start_handler(controller, role, interview_type, company, language):

    response = start_interview(
        controller,
        role,
        interview_type,
        company,
        language,
    )

    return response.to_gradio_outputs()
