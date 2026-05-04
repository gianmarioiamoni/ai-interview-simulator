# app/ui/bindings/orchestrators/ui_event_orchestrator.py

import gradio as gr

from app.ui.handlers.start_handler import start_handler
from app.ui.handlers.report_handler import view_report_handler
from app.ui.state_handlers import (
    submit_answer,
    retry_answer,
    next_question,
)
from app.ui.state_handlers.export_handlers import (
    export_pdf_handler,
    export_json_handler,
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

        # ✅ DEBUG CRITICO
        from app.ui.ui_response import UIResponse

        dummy = UIResponse(state=None)
        expected = len(self.outputs)
        actual = len(dummy.to_gradio_outputs())

        print("\n=== OUTPUT CONTRACT CHECK ===")
        print("UIOutputsBuilder:", expected)
        print("UIResponse:", actual)
        print("=============================\n")

        if expected != actual:
            raise RuntimeError(f"❌ OUTPUT MISMATCH: {expected} != {actual}")

        self.handler_factory = StreamingHandlerFactory(self.outputs)

    def bind(self) -> None:
        self._bind_validation()
        self._bind_start()
        self._bind_submit()
        self._bind_enable_submit()
        self._bind_navigation()
        self._bind_exports()

    # =========================================================
    # VALIDATION (START BUTTON)
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
    # START
    # =========================================================

    def _bind_start(self):
        handler = self.handler_factory.create(
            start_handler,
            "⏳ Generating interview...",
        )

        self.c.start_button.click(
            handler,
            inputs=[
                self.c.role_input,
                self.c.interview_type_input,
                self.c.company_input,
                self.c.language_input,
            ],
            outputs=self.outputs,
        )

    # =========================================================
    # SUBMIT
    # =========================================================

    def _bind_submit(self):
        handler = self.handler_factory.create(
            submit_answer,
            "⏳ Evaluating answer...",
        )

        self.c.submit_button.click(
            handler,
            inputs=[self.state, self.c.written_box],
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
            outputs=self.c.submit_button,
        )

        self.c.coding_box.change(
            enabler.enable,
            inputs=[self.c.coding_box],
            outputs=self.c.submit_button,
        )

        self.c.database_box.change(
            enabler.enable,
            inputs=[self.c.database_box],
            outputs=self.c.submit_button,
        )

    # =========================================================
    # NAVIGATION
    # =========================================================

    def _bind_navigation(self):
        retry_handler = self.handler_factory.create(
            retry_answer,
            "⏳ Retrying...",
        )

        next_handler = self.handler_factory.create(
            next_question,
            "⏳ Loading next question...",
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

    # =========================================================
    # EXPORT
    # =========================================================

    def _bind_exports(self):
        self.c.next_button.click(
            lambda x: x,
            inputs=[self.state],
            outputs=self.state,
        )
