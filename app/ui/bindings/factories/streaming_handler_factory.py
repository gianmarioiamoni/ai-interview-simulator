# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
import time
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.output_count = len(outputs)
        self.loader_index = self.output_count - 1

        # solo questi componenti supportano interactive
        self.button_indices = {14, 15, 16}

    # ---------------------------------------------------------
    # IDLE STATE
    # ---------------------------------------------------------

    def _idle_updates(self) -> List[Any]:
        return [None] * self.output_count

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, response: Any) -> List[Any]:

        # -----------------------------------------------------
        # NONE → NO UPDATE
        # -----------------------------------------------------

        if response is None:
            return self._idle_updates()

        # -----------------------------------------------------
        # ALWAYS RESOLVE TO UIResponse
        # -----------------------------------------------------

        if not isinstance(response, UIResponse):
            response = build_ui_response_from_state(response)

        # -----------------------------------------------------
        # BUILD OUTPUT ARRAY
        # -----------------------------------------------------

        out = list(response.to_gradio_outputs())

        if len(out) != self.output_count:
            raise RuntimeError(
                f"UIResponse output length mismatch: "
                f"{len(out)} != {self.output_count}"
            )

        # -----------------------------------------------------
        # STATE SAFETY (CRITICAL)
        # -----------------------------------------------------

        # se state=None → non toccare lo state UI
        if out[0] is None:
            out[0] = gr.update()

        # -----------------------------------------------------
        # CLEANUP (GRADIO SAFETY)
        # -----------------------------------------------------

        for i, v in enumerate(out):
            if isinstance(v, dict):

                # evita reset value=None
                if v.get("value") is None:
                    v.pop("value", None)

                # evita crash su componenti non compatibili
                if "interactive" in v and i not in self.button_indices:
                    v.pop("interactive", None)

        return out

    # ---------------------------------------------------------
    # FACTORY
    # ---------------------------------------------------------

    def create(
        self,
        action_fn: Callable[..., Any],
        steps: List[str] | None = None,
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # -------------------------------------------------
            # LOADER STEPS
            # -------------------------------------------------

            if steps:
                for step in steps:
                    updates = self._idle_updates()
                    updates[self.loader_index] = show_loader(step)
                    yield tuple(updates)
                    time.sleep(0.35)
            else:
                updates = self._idle_updates()
                updates[self.loader_index] = show_loader("Processing...")
                yield tuple(updates)

            # -------------------------------------------------
            # EXECUTE
            # -------------------------------------------------

            response = action_fn(*args)

            # -------------------------------------------------
            # STREAMING (generator)
            # -------------------------------------------------

            if isinstance(response, Generator):
                for chunk in response:
                    out = self._normalize(chunk)
                    yield tuple(out)
                return

            # -------------------------------------------------
            # SINGLE RESPONSE
            # -------------------------------------------------

            out = self._normalize(response)

            # hide loader SOLO alla fine
            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
