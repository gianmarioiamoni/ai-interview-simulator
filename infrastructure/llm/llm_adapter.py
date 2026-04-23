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

    # ---------------------------------------------------------
    # GENERIC INVOKE (TEXT)
    # ---------------------------------------------------------

    def invoke(self, prompt: str) -> LLMResponse:

        messages = [
            SystemMessage(
                content=(
                    "You are a senior technical interviewer. "
                    "Provide clear, concise, and complete answers."
                )
            ),
            HumanMessage(content=prompt),
        ]

        try:
            raw = self._llm.invoke(messages)
            content = getattr(raw, "content", "") or ""
            return _LangChainResponse(content=content)

        except Exception as e:
            print("\n🔥 LLM INVOCATION FAILED 🔥")
            print(str(e))
            raise

    # ---------------------------------------------------------
    # JSON INVOKE (STRICT FORMAT)
    # ---------------------------------------------------------

    def invoke_json(self, prompt: str) -> LLMResponse:

        messages = [
            SystemMessage(
                content=(
                    "You must return STRICT JSON only. "
                    "No explanations, no markdown, no extra text. "
                    "Output must start with '{' and end with '}'."
                )
            ),
            HumanMessage(content=prompt),
        ]

        try:
            raw = self._llm.invoke(messages)
            content = getattr(raw, "content", "") or ""
            return _LangChainResponse(content=content)

        except Exception as e:
            print("\n🔥 LLM JSON INVOCATION FAILED 🔥")
            print(str(e))
            raise


# ---------------------------------------------------------
# PORT
# ---------------------------------------------------------


class LLMPort(Protocol):

    def invoke(self, prompt: str) -> LLMResponse: ...

    def invoke_json(self, prompt: str) -> LLMResponse: ...
