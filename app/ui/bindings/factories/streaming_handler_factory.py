# app/ui/bindings/factories/streaming_handler_factory.py

import gradio as gr
from typing import Callable, Any, Generator, List

from app.ui.ui_response import UIResponse
from app.ui.utils.loading_utils import show_loader, hide_loader


class StreamingHandlerFactory:
    def __init__(self, outputs: List[Any]):
        self.outputs = outputs
        self.loader_index = len(outputs) - 1  # più robusto

    def _idle_updates(self) -> List[Any]:
        return [gr.update() for _ in range(len(self.outputs))]

    def _normalize(self, response: Any) -> List[Any]:
        if isinstance(response, UIResponse):
            return list(response.to_gradio_outputs())
        return response

    def create(
        self,
        action_fn: Callable[..., Any],
        loader_message: str,
    ) -> Callable[..., Generator[Any, None, None]]:

        def handler(*args: Any):

            updates = self._idle_updates()
            updates[self.loader_index] = show_loader(loader_message)

            yield tuple(updates)

            response = action_fn(*args)

            out = self._normalize(response)
            out[self.loader_index] = hide_loader()

            yield tuple(out)

        return handler
