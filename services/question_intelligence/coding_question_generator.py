# services/question_intelligence/coding_question_generator.py

import json
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.config.settings import settings
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION

from app.core.logger import get_logger

from services.question_intelligence.coding_llm_json_repair import repair_llm_json_text

logger = get_logger(__name__)

# Re-exported for backward compatibility with test imports.
MAX_INVALID_JSON_ATTEMPTS = settings.coding_json_retry_attempts

INVALID_JSON_PREFIX = "Invalid JSON from LLM:"


# =========================================================
# DTOs (Structured Output)
# =========================================================


class GeneratedTestCase(BaseModel):
    args: List = Field(default_factory=list)
    expected: object


class GeneratedCodingQuestion(BaseModel):
    prompt: str
    coding_spec: CodingSpec
    visible_tests: List[GeneratedTestCase]


# =========================================================
# Generator
# =========================================================


class CodingQuestionGenerator:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
        theme_guidance: str | None = None,
    ) -> List[GeneratedCodingQuestion]:

        prompt = self._build_generation_prompt(
            role=role.value,
            level=level.value,
            n=n,
            theme_guidance=theme_guidance,
        )

        parsed = self._invoke_parse_with_retry(
            prompt=prompt,
            log_prefix="[Coding generate]",
        )

        if not parsed:
            logger.warning(
                "[Coding generate] No coding questions produced after parse/retry",
            )
            return []

        return parsed

    # -----------------------------------------------------

    def enrich_from_prompt(
        self,
        seed_prompt: str,
        role: RoleType,
        level: SeniorityLevel,
        provenance: QuestionProvenance | None = None,
        theme_guidance: str | None = None,
    ) -> GeneratedCodingQuestion | None:

        _ = provenance

        prompt = self._build_enrichment_prompt(
            seed_prompt=seed_prompt,
            role=role.value,
            level=level.value,
            theme_guidance=theme_guidance,
        )

        parsed = self._invoke_parse_with_retry(
            prompt=prompt,
            log_prefix="[Coding enrich]",
        )

        if not parsed:
            logger.warning(
                "[Coding enrich] Failed to parse enrichment response after retry",
            )
            return None

        return parsed[0]

    # =========================================================
    # INTERNALS
    # =========================================================

    def _invoke_parse_with_retry(
        self,
        prompt: str,
        log_prefix: str,
    ) -> List[GeneratedCodingQuestion]:

        for attempt in range(1, MAX_INVALID_JSON_ATTEMPTS + 1):

            with LLMOperationContext.scope(QUESTION_GENERATION):
                response = self._llm.invoke(prompt)

            try:
                return self._parse_llm_response(response.content)

            except ValueError as exc:

                if _is_invalid_json_error(exc):

                    if attempt < MAX_INVALID_JSON_ATTEMPTS:
                        logger.warning(
                            f"{log_prefix} Invalid JSON "
                            f"(attempt {attempt}/{MAX_INVALID_JSON_ATTEMPTS}), "
                            f"retrying: {exc}",
                        )
                        continue

                    logger.warning(
                        f"{log_prefix} Invalid JSON after "
                        f"{MAX_INVALID_JSON_ATTEMPTS} attempts: {exc}",
                    )
                    return []

                logger.warning(
                    f"{log_prefix} Parse/validation failed (no retry): {exc}",
                )
                return []

        return []

    def _parse_llm_response(
        self,
        content: str,
    ) -> List[GeneratedCodingQuestion]:

        repaired = repair_llm_json_text(content)

        try:
            raw_data = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{INVALID_JSON_PREFIX} {exc}") from exc

        if not isinstance(raw_data, list):
            raise ValueError("LLM response must be a JSON array")

        validated_items: List[GeneratedCodingQuestion] = []

        for item in raw_data:
            try:
                validated = GeneratedCodingQuestion.model_validate(item)

                if not validated.visible_tests:
                    raise ValueError(
                        "Coding question must include at least one test case",
                    )

                validated_items.append(validated)

            except (ValidationError, ValueError) as exc:
                raise ValueError(
                    f"Invalid coding question structure: {exc}",
                ) from exc

        return validated_items

    def _build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
        theme_guidance: str | None = None,
    ) -> str:

        theme_block = ""

        if theme_guidance:
            theme_block = f"\nTHEME GUIDANCE:\n{theme_guidance}\n"

        template = PromptLoader.load("generation/coding_question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "level": level,
                "role": role,
                "theme_block": theme_block,
                "json_output_contract": self._json_output_contract(),
            },
        )

    def _build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
        theme_guidance: str | None = None,
    ) -> str:

        theme_block = ""

        if theme_guidance:
            theme_block = f"\nTHEME GUIDANCE:\n{theme_guidance}\n"

        template = PromptLoader.load("generation/coding_question_enrichment.txt")

        return PromptRenderer.render(
            template,
            {
                "seed_prompt": seed_prompt,
                "level": level,
                "role": role,
                "theme_block": theme_block,
                "json_output_contract": self._json_output_contract(),
            },
        )

    def _json_output_contract(self) -> str:

        return """
Return STRICT JSON array:

[
  {
    "prompt": "...",

    "coding_spec": {
      "type": "function",
      "entrypoint": "function_name",
      "parameters": ["param1", "param2"]
    },

    "visible_tests": [
      {
        "args": [...],
        "expected": ...
      }
    ]
  }
]
"""


def _is_invalid_json_error(exc: ValueError) -> bool:
    return str(exc).startswith(INVALID_JSON_PREFIX)
