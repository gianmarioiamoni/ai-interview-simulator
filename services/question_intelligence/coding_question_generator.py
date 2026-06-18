# services/question_intelligence/coding_question_generator.py

from typing import List

from pydantic import BaseModel, Field

from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from app.ports.llm_port import LLMPort

from app.core.logger import get_logger

# Re-exported for backward compatibility with test imports.
from services.question_intelligence.coding_response_parser import (
    MAX_INVALID_JSON_ATTEMPTS,
    INVALID_JSON_PREFIX,
    _is_invalid_json_error,
)

logger = get_logger(__name__)


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
    """
    Coordinates coding question generation and enrichment.

    Delegates prompt construction to CodingPromptBuilder and
    LLM invocation + parsing to CodingResponseParser.

    Accepts an optional CodingDomainProfile for BusinessContext-driven
    vocabulary and scenario framing.
    """

    def __init__(self, llm: LLMPort, domain_profile=None) -> None:
        self._llm = llm

        from services.question_intelligence.coding_prompt_builder import (
            CodingPromptBuilder,
        )
        from services.question_intelligence.coding_response_parser import (
            CodingResponseParser,
        )

        self._prompt_builder = CodingPromptBuilder(domain_profile=domain_profile)
        self._response_parser = CodingResponseParser(llm)

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> List[GeneratedCodingQuestion]:

        prompt = self._prompt_builder.build_generation_prompt(
            role=role.value,
            level=level.value,
            n=n,
            theme_guidance=theme_guidance,
            job_description=job_description,
            company_description=company_description,
        )

        parsed = self._response_parser.invoke_and_parse(
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
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> GeneratedCodingQuestion | None:

        _ = provenance

        prompt = self._prompt_builder.build_enrichment_prompt(
            seed_prompt=seed_prompt,
            role=role.value,
            level=level.value,
            theme_guidance=theme_guidance,
            job_description=job_description,
            company_description=company_description,
        )

        parsed = self._response_parser.invoke_and_parse(
            prompt=prompt,
            log_prefix="[Coding enrich]",
        )

        if not parsed:
            logger.warning(
                "[Coding enrich] Failed to parse enrichment response after retry",
            )
            return None

        return parsed[0]
