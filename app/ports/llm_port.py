# app/ports/llm_port.py

from typing import Protocol


class LLMPort(Protocol):
    def invoke(self, prompt: str): ...
