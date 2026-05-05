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
        start_steps = [
            "🧠 Generating interview structure...",
            "📚 Creating questions...",
            "🧪 Preparing test cases...",
            "⚙️ Finalizing interview...",
        ]
        
        start_handler_wrapper = self.handler_factory.create(
            start_handler,
            start_steps,
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
        ).then(
            lambda: gr.update(interactive=False, value="Start Interview"),
            outputs=[self.c.start_button],
        )

    # =========================================================
    # SUBMIT
    # =========================================================

    def _bind_submit(self):
        submit_steps = [
            "🔍 Evaluating answer...",
            "📝 Providing feedback...",
            "💡 Suggesting improvements...",
        ]
        submit_handler_wrapper = self.handler_factory.create(
            submit_answer,
            submit_steps,
        )

        self.c.submit_button.click(
            submit_handler_wrapper,
            inputs=[self.state, self.c.written_box],
            outputs=self.outputs,
            show_progress=False,
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
        retry_steps = [
            "🔄 Retrying...",
            "💡 Suggesting improvements...",
            "📝 Providing feedback...",
        ]
        retry_handler_wrapper = self.handler_factory.create(
            retry_answer,
            retry_steps,
        )

        next_steps = [
            "🔄 Loading next question...",
            "📝 Providing feedback...",
            "💡 Suggesting improvements...",
        ]
        
        next_handler_wrapper = self.handler_factory.create(
            next_question,
            next_steps,
        )

        self.c.retry_button.click(
            retry_handler_wrapper,
            inputs=[self.state],
            outputs=self.outputs,
            show_progress=False,
        )

        self.c.next_button.click(
            next_handler_wrapper,
            inputs=[self.state],
            outputs=self.outputs,
            show_progress=False,
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def _bind_exports(self):
        self.c.next_button.click(
            lambda x: x,
            inputs=[self.state],
            outputs=self.state,
            show_progress=False,
        )
