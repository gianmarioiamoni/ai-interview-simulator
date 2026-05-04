# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.output_count = len(outputs)
        self.loader_index = self.output_count - 1

    # ---------------------------------------------------------
    # IDLE STATE
    # ---------------------------------------------------------

    def _idle_updates(self) -> List[Any]:
        return [None] * self.output_count

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, response: Any) -> List[Any]:
        if isinstance(response, UIResponse):
            out = list(response.to_gradio_outputs())

            # 🔒 HARD SAFETY CHECK
            if len(out) != self.output_count:
                raise RuntimeError(
                    f"UIResponse output length mismatch: "
                    f"{len(out)} != {self.output_count}"
                )

            return out

        return response

    # ---------------------------------------------------------
    # FACTORY
    # ---------------------------------------------------------

    def create(
        self,
        action_fn: Callable[..., Any],
        loader_message: str,
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # -------------------------------------------------
            # STEP 1 — SHOW LOADER
            # -------------------------------------------------

            updates = self._idle_updates()
            updates[self.loader_index] = show_loader(loader_message)

            yield tuple(updates)

            # -------------------------------------------------
            # STEP 2 — EXECUTE ACTION
            # -------------------------------------------------

            response = action_fn(*args)

            # support generator (future proof)
            if isinstance(response, Generator):
                for chunk in response:
                    out = self._normalize(chunk)
                    yield tuple(out)
                return

            out = self._normalize(response)

            # -------------------------------------------------
            # STEP 3 — HIDE LOADER
            # -------------------------------------------------

            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
