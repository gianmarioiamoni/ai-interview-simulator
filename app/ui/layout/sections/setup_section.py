# sections/setup_section.py

import gradio as gr
from app.ui.views.setup_view import SetupView


def render_setup_section():

    with gr.Column(visible=True) as setup_section:

        setup_view = SetupView()

        (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
            start_loading_text,
        ) = setup_view.render()

    return dict(
        setup_section=setup_section,
        role_dropdown=role_dropdown,
        interview_type_radio=interview_type_radio,
        company_input=company_input,
        language_dropdown=language_dropdown,
        start_button=start_button,
        start_loading_text=start_loading_text,
    )
