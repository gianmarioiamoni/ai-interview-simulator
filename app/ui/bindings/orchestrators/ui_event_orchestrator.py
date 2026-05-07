# app/ui/bindings/orchestrators/ui_event_orchestrator.py

import gradio as gr

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.report_handler import view_report_handler

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

        # 🔥 IMPORTANTE
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

        # 👇 wrapper per generator
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
    # ENABLE SUBMIT
    # =========================================================

    def _bind_enable_submit(self):
        enabler = SubmitEnabler()

        current_question_type = self.state.current_question.type
        if current_question_type == "written":
            self.c.written_box.change(
                enabler.enable,
                inputs=[self.c.written_box],
                outputs=self.c.submit_button,
            )
        elif current_question_type == "coding":
            self.c.coding_box.change(
                enabler.enable,
                inputs=[self.c.coding_box],
                outputs=self.c.submit_button,
            )
        elif current_question_type == "database":
            self.c.database_box.change(
                enabler.enable,
                inputs=[self.c.database_box],
                outputs=self.c.submit_button,
            )
        else:
            raise ValueError(f"Unsupported question type: {current_question_type}")

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
