# app/ui/bindings/factories/streaming_handler_factory.py

from typing import Callable, List


class StreamingHandlerFactory:

    def __init__(self, outputs):
        self.outputs = outputs

    def create(self, handler: Callable, _steps: List[str]):

        def wrapper(*args):

            generator = handler(*args)

            if not hasattr(generator, "__iter__"):
                return generator

            for result in generator:
                yield result

        return wrapper
