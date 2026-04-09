# app/ui/handlers/start_handler.py

import gradio as gr

from app.ui.state_handlers import start_interview


def start_handler(role, interview_type, company, language):

    # STEP 1 → show loader WITHOUT changing view
    yield (
        None,
        "",
        "",
        "",
        "",
        "",
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(visible=True),  # setup_section still visible
        gr.update(visible=False),  # interview_section still hidden
        gr.update(),
        gr.update(),
        "",
        "",
        gr.update(),
        gr.update(),
        gr.update(),
        "",
        "",
        "",
        # loader 
        gr.update(value="⏳ Generating interview...", visible=True),
    )

    # STEP 2 → real logic
    response = start_interview(
        role=role,
        interview_type=interview_type,
        company=company,
        language=language,
    )

    # STEP 3 → Final UI + hide loader
    outputs = list(response.to_gradio_outputs())

    outputs.append(gr.update(value="", visible=False))

    yield tuple(outputs)
