# app/ui/handlers/start_handler.py

import gradio as gr

from app.ui.state_handlers import start_interview


def start_handler(role, interview_type, company, language):

    # STEP 1 → immediate loader
    yield (
        None,
        "",
        "⏳ Generating interview...",
        "", "", "",
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),

        gr.update(visible=False), # setup section
        gr.update(visible=True),  # interview section
        gr.update(visible=False),
        gr.update(visible=False),

        "", "",
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),

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
