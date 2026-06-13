# infrastructure/llm/llm_adapter.py

import json

from langchain_core.messages import SystemMessage, HumanMessage

from app.ports.llm_port import LLMPort, LLMResponse
from infrastructure.config.settings import settings
from infrastructure.llm.llm_factory import get_raw_llm

from typing import Type, TypeVar, Protocol
from pydantic import BaseModel

from app.core.logger import get_logger

logger = get_logger(__name__)


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
            logger.error("llm_invocation_failed: %s", e)
            raise

    # ---------------------------------------------------------
    # JSON INVOKE (RETRY + SAFE PARSING)
    # ---------------------------------------------------------

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:

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
        # RETRY LOOP
        # -----------------------------------------------------

        _last_attempt = settings.llm_json_retry_attempts - 1

        for attempt in range(settings.llm_json_retry_attempts):

            try:
                raw = self._llm.invoke(messages)
                content = getattr(raw, "content", "") or ""
                content = content.strip()
                last_content = content

                logger.debug(
                    "invoke_json attempt %d: len=%d start=%r end=%r",
                    attempt,
                    len(content),
                    content[:1],
                    content[-1:],
                )

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
                        logger.debug("extract_recovery_failed: %s", e)

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
                        logger.debug("wrap_recovery_failed: %s", e)

                # -------------------------------------------------
                # RETRY (if not last attempt)
                # -------------------------------------------------

                if attempt < _last_attempt:
                    logger.debug("invoke_json: JSON parsing failed, retrying (attempt %d)", attempt)

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

                # last attempt failed → raise
                raise ValueError("Failed to parse LLM JSON output")

            except Exception as e:
                if attempt == _last_attempt:
                    logger.error("llm_json_invocation_failed: %s | raw=%r", e, last_content)
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
