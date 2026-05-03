import gradio as gr
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.output_count = len(outputs)
        self.loader_index = self.output_count - 1  # loader sempre ultimo

    # ---------------------------------------------------------
    # IDLE STATE
    # ---------------------------------------------------------

    def _idle_updates(self) -> List[Any]:
        # None = non toccare nulla → fondamentale per non rompere UI
        return [None for _ in range(self.output_count)]

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
        include_button: bool = False,
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            # -------------------------------------------------
            # STEP 1 — SHOW LOADER
            # -------------------------------------------------

            updates = self._idle_updates()

            # disable button opzionale (PRIMA degli outputs)
            if include_button:
                updates = [gr.update(interactive=False), *updates]

            loader_index = self.loader_index + (1 if include_button else 0)

            updates[loader_index] = show_loader(loader_message)

            yield tuple(updates)

            # -------------------------------------------------
            # STEP 2 — EXECUTE ACTION
            # -------------------------------------------------

            response = action_fn(*args)

            # support eventuale generator (future-proof)
            if isinstance(response, Generator):
                for chunk in response:
                    out = self._normalize(chunk)
                    yield tuple(out)
                return

            out = self._normalize(response)

            # -------------------------------------------------
            # STEP 3 — HIDE LOADER
            # -------------------------------------------------

            if len(out) == self.output_count:
                out[self.loader_index] = hide_loader()

            if include_button:
                out = [gr.update(interactive=True), *out]

            yield tuple(out)

        return handler
