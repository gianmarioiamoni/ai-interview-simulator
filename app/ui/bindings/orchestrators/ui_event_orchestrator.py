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
from app.ui.bindings.validators.submit_enabler import SubmitEnabler


class UIEventOrchestrator:
    def __init__(self, components):
        self.c = components
        self.state = components.state

        self.outputs_builder = UIOutputsBuilder(components)
        self.outputs = self.outputs_builder.build()

        self.handler_factory = StreamingHandlerFactory(self.outputs)

    def bind(self) -> None:
        self._bind_start()
        self._bind_submit()
        self._bind_enable_submit()
        self._bind_navigation()
        self._bind_report()
        self._bind_exports()

    # =========================================================
    # START
    # =========================================================

    def _bind_start(self):
        start_handler_wrapper = self.handler_factory.create(
            start_handler,
            "⏳ Generating interview...",
            include_button=False,
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
        )

    # =========================================================
    # SUBMIT
    # =========================================================

    def _bind_submit(self):
        submit_handler = self.handler_factory.create(
            submit_answer,
            "⏳ Evaluating answer...",
            include_button=True,
        )

        self.c.submit_button.click(
            submit_handler,
            inputs=[self.state, self.c.written_box],
            outputs=[self.c.submit_button, *self.outputs],
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
        retry_handler = self.handler_factory.create(retry_answer, "⏳ Retrying...")

        next_handler = self.handler_factory.create(
            next_question, "⏳ Loading next question..."
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
    # REPORT
    # =========================================================

    def _bind_report(self):
        report_handler = self.handler_factory.create(
            view_report_handler,
            "⏳ Loading report...",
        )

        # ⚠️ ora usiamo output standard (no più section routing)
        self.c.next_button.click(
            report_handler,
            inputs=[self.state],
            outputs=self.outputs,
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def _bind_exports(self):
        self.c.next_button.click(  # placeholder safe binding
            lambda x: x,
            inputs=[self.state],
            outputs=self.state,
        )
