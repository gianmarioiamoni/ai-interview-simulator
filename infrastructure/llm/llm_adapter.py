# infrastructure/llm/llm_adapter.py

from langchain_core.messages import SystemMessage, HumanMessage

from app.ports.llm_port import LLMPort, LLMResponse
from infrastructure.llm.llm_factory import get_raw_llm

from typing import Type, TypeVar, Protocol
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class _LangChainResponse:
    def __init__(self, content: str):
        self.content = content


class DefaultLLMAdapter(LLMPort):

    def __init__(self):
        self._llm = get_raw_llm()

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

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        print("INVOKE_JSON ADAPTER CALLED")

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
            print("\n=== RAW LLM JSON ===")
            print(content)
            print("=== END RAW LLM JSON ===\n")

            try:
                return schema.model_validate_json(content)
            except Exception:
                start = content.find("{")
                end = content.rfind("}")

                if start != -1 and end != -1:
                    json_str = content[start:end+1]
                    return schema.model_validate_json(json_str)
                
                raise

        except Exception as e:
            print("\n LLM JSON INVOCATION FAILED ")
            print(str(e))
            print("RAW:", content)
            raise


# ---------------------------------------------------------
# PORT
# ---------------------------------------------------------

class LLMPort(Protocol):

    def invoke(self, prompt: str) -> LLMResponse: ...

    def invoke_json(self, prompt: str, schema: Type[T]) -> T: ...
