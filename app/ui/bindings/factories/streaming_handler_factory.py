# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
import time
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.output_count = len(outputs)
        self.loader_index = self.output_count - 1

        # setup indices (aligned with UIOutputsBuilder)
        self.setup_indices = [3, 4, 5, 6, 7]

    # ---------------------------------------------------------
    # IDLE STATE (LOCK-AWARE)
    # ---------------------------------------------------------

    def _idle_updates(self, lock_setup: bool = False) -> List[Any]:

        updates = [gr.update() for _ in range(self.output_count)]

        # keep setup locked during streaming
        if lock_setup:
            for idx in self.setup_indices:
                updates[idx] = gr.update(interactive=False)

        return updates

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, response: Any) -> List[Any]:

        if not isinstance(response, UIResponse):
            response = build_ui_response_from_state(response)

        out = list(response.to_gradio_outputs())

        if len(out) != self.output_count:
            raise RuntimeError(
                f"UIResponse output length mismatch: "
                f"{len(out)} != {self.output_count}"
            )

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
            # STEP 1 — LOADER (LOCKED UI)
            # -------------------------------------------------

            if steps:
                for step in steps:
                    updates = self._idle_updates(lock_setup=True)
                    updates[self.loader_index] = show_loader(step)
                    yield tuple(updates)
                    time.sleep(0.35)
            else:
                updates = self._idle_updates(lock_setup=True)
                updates[self.loader_index] = show_loader("Processing...")
                yield tuple(updates)

            # -------------------------------------------------
            # STEP 2 — EXECUTE
            # -------------------------------------------------

            response = action_fn(*args)

            if isinstance(response, Generator):
                for chunk in response:
                    out = self._normalize(chunk)
                    yield tuple(out)
                return

            out = self._normalize(response)

            # -------------------------------------------------
            # prevent value=None
            # -------------------------------------------------

            for i, v in enumerate(out):
                if isinstance(v, dict):
                    if "value" in v and v["value"] is None:
                        del v["value"]

            # -------------------------------------------------
            # STEP 3 — HIDE LOADER
            # -------------------------------------------------

            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
