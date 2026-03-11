# app/ui/bindings/ui_bindings.py

import gradio as gr

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.report_handler import view_report_handler

from app.ui.state_handlers import export_pdf, export_json, submit_answer

from app.graph.interview_graph import InterviewGraph


def bind_events(graph: InterviewGraph, components):
    # Bind UI events to handlers

    c = components
    state = c.state

    role_dropdown = c.role_dropdown
    interview_type_radio = c.interview_type_radio
    company_input = c.company_input
    language_dropdown = c.language_dropdown
    start_button = c.start_button

    # =========================================================
    # INPUT VALIDATION
    # =========================================================

    def validate_inputs(role, interview_type, company, language):

        valid = (
            role is not None
            and interview_type is not None
            and company is not None
            and company.strip() != ""
            and language is not None
        )

        return gr.update(interactive=valid)

    for component in [
        role_dropdown,
        interview_type_radio,
        company_input,
        language_dropdown,
    ]:
        component.change(
            validate_inputs,
            inputs=[
                role_dropdown,
                interview_type_radio,
                company_input,
                language_dropdown,
            ],
            outputs=start_button,
        )

    # =========================================================
    # OUTPUTS
    # =========================================================

    outputs = [
        c.state,
        c.question_counter,
        c.feedback_output,
        c.written_text,
        c.coding_text,
        c.database_text,
        c.written_container,
        c.coding_container,
        c.database_container,
        c.setup_section,
        c.interview_section,
        c.completion_section,
        c.report_section,
        c.final_feedback,
    ]

    # =========================================================
    # START INTERVIEW
    # =========================================================

    start_button.click(
        lambda r, i, comp, l: start_handler(r, i, comp, l),
        inputs=[
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
        ],
        outputs=outputs,
    )

    # =========================================================
    # SUBMIT ANSWERS
    # =========================================================

    c.written_submit.click(
        lambda s, a: submit_answer(s, a),
        inputs=[state, c.written_box],
        outputs=outputs,
    )

    c.coding_submit.click(
        lambda s, a: submit_answer(s, a),
        inputs=[state, c.coding_box],
        outputs=outputs,
    )

    c.database_submit.click(
        lambda s, a: submit_answer(s, a),
        inputs=[state, c.database_box],
        outputs=outputs,
    )

    # =========================================================
    # VIEW REPORT
    # =========================================================

    def report_handler(state_value):
        yield from view_report_handler(graph, state_value)

    c.view_report_button.click(
        report_handler,
        inputs=[state],
        outputs=[
            c.setup_section,
            c.interview_section,
            c.completion_section,
            c.report_section,
            c.report_output,
        ],
        show_progress=True,
    )

    # =========================================================
    # EXPORT PDF
    # =========================================================

    c.pdf_button.click(
        lambda s: (export_pdf(s), gr.update(visible=True)),
        inputs=[state],
        outputs=[c.pdf_file, c.pdf_file],
    )

    # =========================================================
    # EXPORT JSON
    # =========================================================

    c.json_button.click(
        lambda s: (export_json(s), gr.update(visible=True)),
        inputs=[state],
        outputs=[c.json_file, c.json_file],
    )
