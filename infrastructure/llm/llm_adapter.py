# infrastructure/llm/llm_adapter.py
from langchain_core.messages import SystemMessage, HumanMessage

from app.ports.llm_port import LLMPort, LLMResponse
from infrastructure.llm.llm_factory import get_llm

from typing import Protocol

class _LangChainResponse:
    def __init__(self, content: str):
        self.content = content


class DefaultLLMAdapter(LLMPort):

    def invoke(
        self, 
        prompt: str, 
        system_prompt: str | None = None
    ) -> LLMResponse:

        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
           raw = self._llm.invoke(messages)
           content = getattr(raw, "content", "") or ""
           return _LangChainResponse(content=content)

        except Exception as e:
           print("\n🔥 LLM INVOCATION FAILED 🔥")
           print(str(e))
           raise


class LLMPort(Protocol):
    def invoke(
        self, 
        prompt: str, 
        system_prompt: str | None = None
    ) -> LLMResponse: ...
