# app/ui/bindings/orchestrators/ui_event_orchestrator.py

import gradio as gr

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.report_handler import view_report_handler
from app.ui.state_handlers import (
    export_pdf,
    export_json,
    submit_answer,
    retry_answer,
    next_question,
    new_interview,
)

from app.ui.bindings.builders.ui_outputs_builder import UIOutputsBuilder
from app.ui.bindings.factories.streaming_handler_factory import StreamingHandlerFactory
from app.ui.bindings.validators.input_validator import InputValidator
from app.ui.bindings.validators.submit_enabler import SubmitEnabler


class UIEventOrchestrator:
    def __init__(self, components):
        self.c = components
        self.state = components.state

        self.outputs_builder = UIOutputsBuilder(components)
        self.outputs = self.outputs_builder.build()

        self.handler_factory = StreamingHandlerFactory(self.outputs)

    def bind(self) -> None:
        self._bind_validation()
        self._bind_start()
        self._bind_submit()
        self._bind_enable_submit()
        self._bind_navigation()
        self._bind_report()
        self._bind_exports()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _bind_validation(self):
        validator = InputValidator()

        for component in [
            self.c.role_dropdown,
            self.c.interview_type_radio,
            self.c.company_input,
            self.c.language_dropdown,
        ]:
            component.change(
                validator.validate,
                inputs=[
                    self.c.role_dropdown,
                    self.c.interview_type_radio,
                    self.c.company_input,
                    self.c.language_dropdown,
                ],
                outputs=self.c.start_button,
            )

    # =========================================================
    # START
    # =========================================================

    def _bind_start(self):
        self.c.start_button.click(
            start_handler,
            inputs=[
                self.c.role_dropdown,
                self.c.interview_type_radio,
                self.c.company_input,
                self.c.language_dropdown,
            ],
            outputs=self.outputs,
        )

    # =========================================================
    # SUBMIT
    # =========================================================

    def _bind_submit(self):
        submit_handler = self.handler_factory.create(
            submit_answer, "⏳ Evaluating answer..."
        )

        self.c.written_submit.click(
            submit_handler,
            inputs=[self.state, self.c.written_box],
            outputs=self.outputs,
        )

        self.c.coding_submit.click(
            submit_handler,
            inputs=[self.state, self.c.coding_box],
            outputs=self.outputs,
        )

        self.c.database_submit.click(
            submit_handler,
            inputs=[self.state, self.c.database_box],
            outputs=self.outputs,
        )

    # =========================================================
    # ENABLE SUBMIT
    # =========================================================

    def _bind_enable_submit(self):
        enabler = SubmitEnabler()

        self.c.written_box.change(
            enabler.enable,
            inputs=[self.c.written_box],
            outputs=self.c.written_submit,
        )

        self.c.coding_box.change(
            enabler.enable,
            inputs=[self.c.coding_box],
            outputs=self.c.coding_submit,
        )

        self.c.database_box.change(
            enabler.enable,
            inputs=[self.c.database_box],
            outputs=self.c.database_submit,
        )

    # =========================================================
    # NAVIGATION
    # =========================================================

    def _bind_navigation(self):
        retry_handler = self.handler_factory.create(retry_answer, "⏳ Retrying...")

        next_handler = self.handler_factory.create(
            next_question, "⏳ Loading next question..."
        )

        new_interview_handler = self.handler_factory.create(
            lambda *_: new_interview(), "⏳ Starting new interview..."
        )

        self.c.retry_button.click(
            retry_handler,
            inputs=[self.state],
            outputs=self.outputs,
        )

        self.c.next_button.click(
            next_handler,
            inputs=[self.state],
            outputs=self.outputs,
        )

        self.c.new_interview_button.click(
            new_interview_handler,
            inputs=[self.state],
            outputs=self.outputs,
        )

    # =========================================================
    # REPORT
    # =========================================================

    def _bind_report(self):
        report_handler = self.handler_factory.create(
            view_report_handler, "⏳ Loading report..."
        )

        self.c.view_report_button.click(
            report_handler,
            inputs=[self.state],
            outputs=[
                self.c.setup_section,
                self.c.interview_section,
                self.c.completion_section,
                self.c.report_section,
                self.c.report_output,
            ],
            show_progress=True,
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def _bind_exports(self):
        self.c.pdf_button.click(
            lambda s: (export_pdf(s), gr.update(visible=True)),
            inputs=[self.state],
            outputs=[self.c.pdf_file, self.c.pdf_file],
        )

        self.c.json_button.click(
            lambda s: (export_json(s), gr.update(visible=True)),
            inputs=[self.state],
            outputs=[self.c.json_file, self.c.json_file],
        )
