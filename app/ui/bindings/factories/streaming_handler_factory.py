# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
from typing import Callable, Any, Generator, List, Optional

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
        disable_button: Optional[gr.Button] = None, 
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # -------------------------------------------------
            # STEP 1 — INITIAL STATE (disable + loader)
            # -------------------------------------------------

            updates = self._idle_updates()

            # Disable button if required
            if disable_button:
                disable_button = gr.update(interactive=False)
                updates[0] = disable_button 

            # Show loader
            updates = self._idle_updates()
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

            yield tuple(out)

        return handler
