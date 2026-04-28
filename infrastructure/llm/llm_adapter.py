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
    # JSON INVOKE (RETRY + SAFE PARSING)
    # ---------------------------------------------------------

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        print("INVOKE_JSON ADAPTER CALLED")

        base_messages = [
            SystemMessage(
                content=(
                    "You must return STRICT JSON only.\n"
                    "- No explanations\n"
                    "- No markdown\n"
                    "- No extra text\n"
                    "- Output must be a valid JSON object\n"
                    "- Output must start with '{' and end with '}'"
                )
            ),
            HumanMessage(content=prompt),
        ]

        messages = list(base_messages)

        last_content = ""

        # -----------------------------------------------------
        # RETRY LOOP (max 2 attempts)
        # -----------------------------------------------------

        for attempt in range(2):

            try:
                raw = self._llm.invoke(messages)
                content = getattr(raw, "content", "") or ""
                last_content = content

                print("\n=== RAW LLM JSON ===")
                print(content)
                print("=== END RAW LLM JSON ===\n")

                # -------------------------------------------------
                # TRY STRICT PARSE
                # -------------------------------------------------

                try:
                    return schema.model_validate_json(content)
                except Exception:
                    pass

                # -------------------------------------------------
                # RECOVERY 1: extract JSON object
                # -------------------------------------------------

                start = content.find("{")
                end = content.rfind("}")

                if start != -1 and end != -1:
                    json_str = content[start : end + 1]
                    return schema.model_validate_json(json_str)

                # -------------------------------------------------
                # RECOVERY 2: wrap missing braces
                # -------------------------------------------------

                if '"drivers"' in content or '"blockers"' in content:
                    json_str = "{" + content.strip().strip(",") + "}"
                    return schema.model_validate_json(json_str)

                # -------------------------------------------------
                # RETRY (if first attempt)
                # -------------------------------------------------

                if attempt == 0:
                    print("⚠️ JSON parsing failed → retrying with correction prompt")

                    messages.append(
                        HumanMessage(
                            content=(
                                "Your previous response was not valid JSON.\n"
                                "Return ONLY a valid JSON object.\n"
                                "Do not include any text outside JSON."
                            )
                        )
                    )
                    continue

                # second attempt failed → raise
                raise ValueError("Failed to parse LLM JSON output")

            except Exception as e:
                if attempt == 1:
                    print("\n❌ LLM JSON INVOCATION FAILED ❌")
                    print(str(e))
                    print("RAW:", last_content)
                    raise

        # fallback safety (should never reach here)
        raise RuntimeError("Unexpected invoke_json failure")


# ---------------------------------------------------------
# PORT
# ---------------------------------------------------------


class LLMPort(Protocol):

    def invoke(self, prompt: str) -> LLMResponse: ...

    def invoke_json(self, prompt: str, schema: Type[T]) -> T: ...
