# app/ui/bindings/orchestrators/ui_event_orchestrator.py

import gradio as gr

from app.ui.handlers.start_handler import start_handler
from app.ui.state_handlers import export_pdf, export_json, new_interview

from app.ui.state_handlers import (
    submit_answer,
    retry_answer,
    next_question,
)

from app.ui.bindings.builders.ui_outputs_builder import UIOutputsBuilder
from app.ui.bindings.validators.input_validator import InputValidator
from app.ui.bindings.validators.submit_enabler import SubmitEnabler
from app.ui.bindings.factories.streaming_handler_factory import StreamingHandlerFactory


class UIEventOrchestrator:
    def __init__(self, components):
        self.c = components
        self.state = components.state

        self.outputs_builder = UIOutputsBuilder(components)
        self.outputs = self.outputs_builder.build()

        # contract check
        from app.ui.ui_response import UIResponse

        dummy = UIResponse(state=None)
        if len(self.outputs) != len(dummy.to_gradio_outputs()):
            raise RuntimeError("OUTPUT CONTRACT MISMATCH")

        # streaming handler factory
        self.handler_factory = StreamingHandlerFactory(self.outputs)

    def bind(self) -> None:
        self._bind_validation()
        self._bind_start()
        self._bind_submit()
        self._bind_enable_submit()
        self._bind_navigation()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _bind_validation(self):
        validator = InputValidator()

        for component in [
            self.c.role_input,
            self.c.interview_type_input,
            self.c.company_input,
            self.c.language_input,
        ]:
            component.change(
                validator.validate,
                inputs=[
                    self.c.role_input,
                    self.c.interview_type_input,
                    self.c.company_input,
                    self.c.language_input,
                ],
                outputs=self.c.start_button,
            )

    # =========================================================
    # START (STREAMING)
    # =========================================================

    def _bind_start(self):

        start_handler_wrapper = self.handler_factory.create(
            start_handler,
            [
                "Generating interview structure...",
                "Creating questions...",
                "Preparing test cases...",
                "Finalizing interview...",
            ],
        )

        self.c.start_button.click(
            start_handler_wrapper,
            inputs=[
                self.c.role_input,
                self.c.interview_type_input,
                self.c.company_input,
                self.c.language_input,
            ],
            outputs=self.outputs,
            show_progress=False,
        )

    # =========================================================
    # SUBMIT (SYNC)
    # =========================================================

    def _bind_submit(self):
        self.c.submit_button.click(
            submit_answer,
            inputs=[
                self.state,
                self.c.written_box,
                self.c.coding_box,
                self.c.database_box,
            ],
            outputs=self.outputs,
            show_progress=False,
        )

    # =========================================================
    # ENABLE SUBMIT (REACTIVE - CORRETTO)
    # =========================================================

    def _bind_enable_submit(self):
        enabler = SubmitEnabler()

        inputs = [
            self.state,
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,
        ]

        self.c.written_box.change(
            enabler.enable,
            inputs=inputs,
            outputs=self.c.submit_button,
        )

        # coding
        self.c.coding_box.change(
            enabler.enable,
            inputs=inputs,
            outputs=self.c.submit_button,
        )

        # sql
        self.c.database_box.change(
            enabler.enable,
            inputs=inputs,
            outputs=self.c.submit_button,
        )

    # =========================================================
    # NAVIGATION (SYNC)
    # =========================================================

    def _bind_navigation(self):
        self.c.retry_button.click(
            retry_answer,
            inputs=[self.state],
            outputs=self.outputs,
            show_progress=False,
        )

        self.c.next_button.click(
            next_question,
            inputs=[self.state],
            outputs=self.outputs,
            show_progress=False,
        )

        # PDF
        self.c.report_section.pdf_button.click(
            export_pdf,
            inputs=[self.state],
            outputs=self.c.report_section.pdf_file,
        )

        # JSON
        self.c.report_section.json_button.click(
            export_json,
            inputs=[self.state],
            outputs=self.c.json_file,
        )

        # NEW INTERVIEW
        self.c.report_section.new_interview_button.click(
            new_interview,
            inputs=[self.state],
            outputs=self.outputs,
        )
