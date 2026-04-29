# infrastructure/llm/llm_adapter.py

import json

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
                content = content.strip()
                last_content = content

                print("\n=== RAW LLM JSON ===")
                print(content)
                print("=== END RAW LLM JSON ===\n")
                print("LEN:", len(content))
                print("ATTEMPT:", attempt)
                print("START CHAR:", content[:1])
                print("END CHAR:", content[-1:])
                print("FIRST 50:", content[:50])
                print("LAST 50:", content[-50:])

                # -------------------------------------------------
                # TRY STRICT PARSE
                # -------------------------------------------------

                try:
                    parsed = json.loads(content)

                    if isinstance(parsed, dict) and "drivers" in parsed and "blockers" in parsed:
                        parsed = _normalize_decision_schema(parsed)

                    return schema.model_validate(parsed)
                except Exception:
                    pass

                # -------------------------------------------------
                # RECOVERY 1: extract JSON object
                # -------------------------------------------------

                start = content.find("{")
                end = content.rfind("}")

                if start != -1 and end != -1:
                    json_str = content[start : end + 1]
                    try:
                        parsed = json.loads(json_str)

                        if isinstance(parsed, dict) and "drivers" in parsed and "blockers" in parsed:
                            parsed = _normalize_decision_schema(parsed)

                        return schema.model_validate(parsed)
                    except Exception as e:
                        print("⚠️ EXTRACT RECOVERY FAILED:", e)

                # -------------------------------------------------
                # RECOVERY 2: wrap missing braces
                # -------------------------------------------------

                if (
                    ('"drivers"' in content or '"blockers"' in content)
                    and not content.strip().startswith("{")
                ):
                    json_str = "{" + content.strip().strip(",") + "}"
                    try:
                        parsed = json.loads(json_str)

                        if isinstance(parsed, dict) and "drivers" in parsed and "blockers" in parsed:
                            parsed = _normalize_decision_schema(parsed)

                        return schema.model_validate(parsed)
                    except Exception as e:
                        print("⚠️ WRAP RECOVERY FAILED:", e)

                # -------------------------------------------------
                # RETRY (if first attempt)
                # -------------------------------------------------

                if attempt == 0:
                    print("⚠️ JSON parsing failed → retrying with correction prompt")

                    messages = list(base_messages) + [
                        HumanMessage(
                            content=(
                                "Your previous response was not valid JSON.\n"
                                "Return ONLY a valid JSON object.\n"
                                "Do not include any text outside JSON."
                            )
                        )
                    ]
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


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _normalize_decision_schema(data: dict) -> dict:

    def extract(items):
        out = []
        for i in items:
            if isinstance(i, str):
                out.append(i)
            elif isinstance(i, dict):
                text = i.get("justification") or i.get("text")
                if text:
                    out.append(text)
        return out

    return {
        "drivers": extract(data.get("drivers", [])),
        "blockers": extract(data.get("blockers", [])),
    }
