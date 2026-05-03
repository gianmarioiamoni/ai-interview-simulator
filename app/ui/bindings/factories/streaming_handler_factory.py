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

    def _idle_updates(self):
        return [None] * self.output_count

    def _normalize(self, response):
        if isinstance(response, UIResponse):
            return list(response.to_gradio_outputs())
        return response

    def create(self, action_fn, loader_message):

        def handler(*args):

            # STEP 1 — loader
            updates = self._idle_updates()
            updates[self.loader_index] = show_loader(loader_message)
            yield tuple(updates)

            # STEP 2 — execute
            response = action_fn(*args)

            out = self._normalize(response)

            # STEP 3 — hide loader
            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
