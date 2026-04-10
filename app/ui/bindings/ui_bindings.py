# app/ui/bindings/ui_bindings.py

import gradio as gr
from typing import Callable, Any, Generator, List

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.report_handler import view_report_handler
from app.ui.ui_response import UIResponse
from app.ui.ui_state import UIState
from app.ui.state_handlers import (
    export_pdf,
    export_json,
    submit_answer,
    retry_answer,
    next_question,
    new_interview,
)
from app.ui.utils.loading_utils import show_loader, hide_loader


def bind_events(components):
    # Bind UI events to handlers

    c = components
    state = c.state

    role_dropdown = c.role_dropdown
    interview_type_radio = c.interview_type_radio
    company_input = c.company_input
    language_dropdown = c.language_dropdown
    start_button = c.start_button
    start_loading_text = c.start_loading_text

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
    # OUTPUTS (CRITICAL ORDER)
    # =========================================================

    outputs = [
        c.state,
        c.question_counter,
        c.feedback_output,
        # ---------------- DISPLAY
        c.written_display,
        c.coding_display,
        c.database_display,
        # ---------------- CONTAINERS
        c.written_container,
        c.coding_container,
        c.database_container,
        # ---------------- SECTIONS
        c.setup_section,
        c.interview_section,
        c.completion_section,
        c.report_section,
        # ---------------- COMPLETION / REPORT
        c.final_feedback,
        c.report_output,
        # ---------------- BUTTONS
        c.written_submit,
        c.retry_button,
        c.next_button,
        # ---------------- INPUT RESET
        c.written_box,
        c.coding_box,
        c.database_box,
        # ---------------- LOADER
        c.start_loading_text,
    ]

    # =========================================================
    # HANDLER HELPERS 
    # =========================================================

    loader_index = outputs.index(start_loading_text)

    def idle_updates(outputs_len: int) -> List[Any]:
        # 🔥 FIX: evitare lista condivisa
        return [gr.update() for _ in range(outputs_len)]

    def normalize_response(response: Any) -> List[Any]:
        if isinstance(response, UIResponse):
            return list(response.to_gradio_outputs())
        return response

    def build_streaming_handler(
        action_fn: Callable[..., Any],
        loader_message: str,
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # STEP 1 → loader (SINGLE SOURCE OF TRUTH)
            updates = idle_updates(len(outputs))
            updates[loader_index] = show_loader(loader_message)

            yield tuple(updates)

            # STEP 2 → business logic
            response = action_fn(*args)

            # STEP 3 → normalize
            out = normalize_response(response)

            # STEP 4 → hide loader (overwrite, no append!)
            out[loader_index] = hide_loader()

            yield tuple(out)

        return handler

    # =========================================================
    # STREAMING HANDLERS
    # =========================================================

    submit_handler = build_streaming_handler(submit_answer, "⏳ Evaluating answer...")
    next_handler = build_streaming_handler(next_question, "⏳ Loading next question...")
    retry_handler = build_streaming_handler(retry_answer, "⏳ Retrying...")
    new_interview_handler = build_streaming_handler(
        lambda *_: new_interview(), "⏳ Starting new interview..."
    )

    def report_handler(state_value):
        yield from view_report_handler(state_value)

    # =========================================================
    # START INTERVIEW
    # =========================================================

    start_button.click(
        start_handler,
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
        submit_handler,
        inputs=[state, c.written_box],
        outputs=outputs,
    )

    c.coding_submit.click(
        submit_handler,
        inputs=[state, c.coding_box],
        outputs=outputs,
    )

    c.database_submit.click(
        submit_handler,
        inputs=[state, c.database_box],
        outputs=outputs,
    )

    # =========================================================
    # ENABLE SUBMIT WHEN ANSWER IS NOT EMPTY
    # =========================================================

    def enable_submit(text):

        if text and str(text).strip():
            return gr.update(interactive=True)

        return gr.update(interactive=False)

    c.written_box.change(
        enable_submit,
        inputs=[c.written_box],
        outputs=c.written_submit,
    )

    c.coding_box.change(
        enable_submit,
        inputs=[c.coding_box],
        outputs=c.coding_submit,
    )

    c.database_box.change(
        enable_submit,
        inputs=[c.database_box],
        outputs=c.database_submit,
    )

    # =========================================================
    # RETRY ANSWER (FIX: ora con loader)
    # =========================================================

    c.retry_button.click(
        retry_handler,
        inputs=[state],
        outputs=outputs,
    )

    # =========================================================
    # NEXT QUESTION
    # =========================================================

    c.next_button.click(
        next_handler,
        inputs=[state],
        outputs=outputs,
    )

    # =========================================================
    # NEW INTERVIEW
    # =========================================================

    c.new_interview_button.click(
        new_interview_handler,
        inputs=[state],
        outputs=outputs,
    )

    # =========================================================
    # VIEW REPORT (streaming)
    # =========================================================

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
