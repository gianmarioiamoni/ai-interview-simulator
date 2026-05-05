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

    # ---------------------------------------------------------
    # IDLE STATE
    # ---------------------------------------------------------

    def _idle_updates(self) -> List[Any]:
        # None = non toccare il componente
        return [None] * self.output_count

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize(self, response: Any) -> List[Any]:

        if isinstance(response, UIResponse):
            out = list(response.to_gradio_outputs())

            if len(out) != self.output_count:
                raise RuntimeError(
                    f"UIResponse output length mismatch: "
                    f"{len(out)} != {self.output_count}"
                )

            return out

        # fallback safety
        if isinstance(response, list):
            return response

        raise RuntimeError(f"Unsupported response type: {type(response)}")

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
            # STEP 1 — MULTI-STEP LOADER (CONTROLLED TIMING)
            # -------------------------------------------------

            if steps:
                for step in steps:
                    updates = self._idle_updates()
                    updates[self.loader_index] = show_loader(step)
                    yield tuple(updates)

                    # 🔥 CRUCIALE: tempo minimo per UX
                    time.sleep(0.35)

            else:
                # fallback loader base
                updates = self._idle_updates()
                updates[self.loader_index] = show_loader("Processing...")
                yield tuple(updates)

            # -------------------------------------------------
            # STEP 2 — EXECUTE ACTION
            # -------------------------------------------------

            response = action_fn(*args)

            # -------------------------------------------------
            # STEP 2.1 — STREAM SUPPORT (FUTURE-PROOF)
            # -------------------------------------------------

            if isinstance(response, Generator):
                for chunk in response:
                    out = self._normalize(chunk)
                    yield tuple(out)
                return

            # -------------------------------------------------
            # STEP 2.2 — NORMAL RESPONSE
            # -------------------------------------------------

            out = self._normalize(response)
            # avoid override value of buttons
            for i, v in enumerate(out):
                if isinstance(v, dict) and "value" in v and v["value"] is None:
                    v.pop("value")

            # -------------------------------------------------
            # STEP 3 — HIDE LOADER
            # -------------------------------------------------

            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
