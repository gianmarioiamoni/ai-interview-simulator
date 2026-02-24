# infrastructure/llm/llm_adapter.py

from app.ports.llm_port import LLMPort, LLMResponse
from infrastructure.llm.llm_factory import get_llm

from typing import Protocol

class _LangChainResponse:
    def __init__(self, content: str):
        self.content = content


class DefaultLLMAdapter(LLMPort):

    def __init__(self):
        self._llm = get_llm()

    def invoke(self, prompt: str) -> LLMResponse:
        raw = self._llm.invoke(prompt)
        return _LangChainResponse(content=raw.content)


class LLMPort(Protocol):
    def invoke(self, prompt: str, temperature: float = 0.0) -> LLMResponse: ...
