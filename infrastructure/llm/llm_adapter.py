# infrastructure/llm/llm_adapter.py
from langchain_core.messages import SystemMessage, HumanMessage

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
        messages = [
            SystemMessage(
                content=(
                    "You must return STRICT JSON only."
                    "No explanations, no markdown, no extra text."
                    "Output must start with '{' and end with '}'."
                )
            ),
            HumanMessage(content=prompt),
        ]
        raw = self._llm.invoke(messages)

        return _LangChainResponse(content=raw.content)


class LLMPort(Protocol):
    def invoke(self, prompt: str, temperature: float = 0.0) -> LLMResponse: ...
