# app/ui/bindings/ui_bindings.py

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.submit_handler import submit_handler
from app.ui.handlers.report_handler import view_report_handler

from app.ui.state_handlers import export_pdf, export_json


def bind_events(controller, components):
    # Bind events to handlers

    state = components["state"]

    start_button = components["start_button"]

    role_dropdown = components["role_dropdown"]
    interview_type_radio = components["interview_type_radio"]
    company_input = components["company_input"]
    language_dropdown = components["language_dropdown"]

    outputs = [
        components["state"],
        components["question_counter"],
        components["feedback_output"],
        components["written_text"],
        components["coding_text"],
        components["database_text"],
        components["written_container"],
        components["coding_container"],
        components["database_container"],
        components["setup_section"],
        components["interview_section"],
        components["completion_section"],
        components["report_section"],
        components["final_feedback"],
    ]

    start_button.click(
        lambda r, i, c, l: start_handler(controller, r, i, c, l),
        inputs=[role_dropdown, interview_type_radio, company_input, language_dropdown],
        outputs=outputs,
    )

    components["written_submit"].click(
        lambda s, a: submit_handler(controller, s, a),
        inputs=[state, components["written_box"]],
        outputs=outputs,
    )

    components["coding_submit"].click(
        lambda s, a: submit_handler(controller, s, a),
        inputs=[state, components["coding_box"]],
        outputs=outputs,
    )

    components["database_submit"].click(
        lambda s, a: submit_handler(controller, s, a),
        inputs=[state, components["database_box"]],
        outputs=outputs,
    )

    components.view_report_button.click(
        lambda s: view_report_handler(controller, s),
        inputs=[state],
        outputs=[
            components.setup_section,
            components.interview_section,
            components.completion_section,
            components.report_section,
            components.report_output,
        ],
    )

    components.pdf_button.click(
        lambda s: (export_pdf(controller, s), gr.update(visible=True)),
        inputs=[state],
        outputs=[components.pdf_file, components.pdf_file],
    )

    components.json_button.click(
        lambda s: (export_json(controller, s), gr.update(visible=True)),
        inputs=[state],
        outputs=[components.json_file, components.json_file],
    )