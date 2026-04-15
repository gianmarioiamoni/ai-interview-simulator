# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.loader_index = len(outputs) - 1  # robust: loader sempre ultimo

    # ---------------------------------------------------------
    # IDLE STATE
    # ---------------------------------------------------------

    def _idle_updates(self) -> List[Any]:
        return [gr.update() for _ in range(len(self.outputs))]

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, response: Any) -> List[Any]:
        if isinstance(response, UIResponse):
            return list(response.to_gradio_outputs())
        return response

    # ---------------------------------------------------------
    # FACTORY
    # ---------------------------------------------------------

    def create(
        self,
        action_fn: Callable[..., Any],
        loader_message: str,
        disable_first_output: bool = False,  # 👈 NEW
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # -------------------------------------------------
            # STEP 1 — INITIAL STATE (disable + loader)
            # -------------------------------------------------

            updates = self._idle_updates()

            # Disable first output if required (button)
            if disable_first_output:
                updates[0] = gr.update(interactive=False)

            # Show loader
            updates[self.loader_index] = show_loader(loader_message)

            yield tuple(updates)

            # -------------------------------------------------
            # STEP 2 — EXECUTE ACTION
            # -------------------------------------------------

            response = action_fn(*args)

            out = self._normalize(response)

            # -------------------------------------------------
            # STEP 3 — FINAL STATE (hide loader)
            # -------------------------------------------------

            out[self.loader_index] = hide_loader()

            # Keep button disabled after execution
            if disable_first_output:
                out[0] = gr.update(interactive=False)

            yield tuple(out)

        return handler
