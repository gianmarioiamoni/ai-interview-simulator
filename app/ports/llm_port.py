# app/ports/llm_port.py

from typing import Protocol


class LLMResponse(Protocol):
    content: str


class LLMPort(Protocol):
    def invoke(self, prompt: str) -> LLMResponse: ...
