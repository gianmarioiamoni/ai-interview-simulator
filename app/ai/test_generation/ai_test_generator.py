# app/ai/test_generation/ai_test_generator.py

import json
from typing import List, Any

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.question.question import Question
from domain.contracts.execution.coding_spec import CodingSpec

from app.ports.llm_port import LLMPort
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION
from app.ai.test_generation.test_cache_service import TestCacheService
from app.ai.test_generation.test_diversity_filter import TestDiversityFilter
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from app.core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# DTO
# =========================================================


class GeneratedTestCase(BaseModel):
    args: list = Field(default_factory=list)
    expected: Any


# =========================================================
# GENERATOR
# =========================================================


class AITestGenerator:

    def __init__(self, llm: LLMPort):
        self._llm = llm
        self._cache = TestCacheService()
        self._diversity_filter = TestDiversityFilter()

    # =========================================================

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
    ) -> List[CodingTestCase]:

        if not question.coding_spec:
            raise ValueError("CodingSpec required for test generation")

        # -----------------------------------------------------
        # CACHE
        # -----------------------------------------------------

        cached = self._cache.get_tests(question, num_tests)
        if cached:
            return cached

        # -----------------------------------------------------
        # GENERATION (RETRY)
        # -----------------------------------------------------

        tests: List[CodingTestCase] = []

        for attempt in range(2):

            tests = self._generate_with_llm(
                question,
                num_tests * 2,
                retry=(attempt == 1),
            )

            tests = self._validate_tests_against_spec(
                tests,
                question.coding_spec,
            )

            if tests:
                break

            logger.warning(f"test_generation_empty_attempt_{attempt}")

        # -----------------------------------------------------
        # FALLBACK (CRITICAL)
        # -----------------------------------------------------

        if not tests:
            logger.warning("LLM test generation failed → using fallback")
            tests = self._fallback_tests(question.coding_spec)

        # -----------------------------------------------------
        # DIVERSITY
        # -----------------------------------------------------

        tests = self._diversity_filter.filter(tests, num_tests)

        # -----------------------------------------------------
        # CACHE STORE
        # -----------------------------------------------------

        self._cache.store_tests(question, num_tests, tests)

        return tests

    # =========================================================
    # LLM GENERATION
    # =========================================================

    def _generate_with_llm(
        self,
        question: Question,
        num_tests: int,
        retry: bool = False,
    ) -> List[CodingTestCase]:

        spec = question.coding_spec

        prompt = self._build_prompt(
            question.prompt,
            spec,
            num_tests,
        )

        if retry:
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON."

        with LLMOperationContext.scope(QUESTION_GENERATION):
            response = self._llm.invoke(prompt)

        content = response.content or ""

        raw_data = self._safe_json_parse(content)

        if not isinstance(raw_data, list):
            logger.warning("LLM output is not a list")
            return []

        tests: List[CodingTestCase] = []

        for item in raw_data:

            try:
                validated = GeneratedTestCase.model_validate(item)

                tests.append(
                    CodingTestCase(
                        args=validated.args,
                        kwargs={},  # enforce consistency
                        expected=validated.expected,
                    )
                )

            except ValidationError:
                continue

        return tests

    # =========================================================
    # SAFE JSON PARSE (KEY HARDENING)
    # =========================================================

    def _safe_json_parse(self, content: str):

        # 1. Try direct
        try:
            return json.loads(content)
        except Exception:
            pass

        # 2. Extract JSON block
        start = content.find("[")
        end = content.rfind("]")

        if start != -1 and end != -1:
            try:
                return json.loads(content[start : end + 1])
            except Exception:
                pass

        # 3. Remove markdown fences
        content = content.replace("```json", "").replace("```", "")

        try:
            return json.loads(content)
        except Exception:
            logger.warning("Failed to parse LLM JSON output")
            return []

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_tests_against_spec(
        self,
        tests: List[CodingTestCase],
        spec: CodingSpec,
    ) -> List[CodingTestCase]:

        expected_len = len(spec.parameters)

        valid = []

        for t in tests:

            # strict length
            if len(t.args) != expected_len:
                continue

            # basic sanity: no None args
            if any(arg is None for arg in t.args):
                continue

            valid.append(t)

        return valid

    # =========================================================
    # FALLBACK (CRITICAL FOR UX)
    # =========================================================

    def _fallback_tests(self, spec: CodingSpec) -> List[CodingTestCase]:

        num_params = len(spec.parameters)

        # simple deterministic fallback
        base_args = [0] * num_params

        return [
            CodingTestCase(args=base_args, expected=0),
            CodingTestCase(args=[1] * num_params, expected=1),
        ]

    # =========================================================
    # PROMPT
    # =========================================================

    def _build_prompt(
        self,
        prompt: str,
        spec: CodingSpec,
        num_tests: int,
    ) -> str:

        template = PromptLoader.load("test_generation/ai_test_generator.txt")

        context = {
            "problem": prompt,
            "entrypoint": spec.entrypoint,
            "parameters": json.dumps(spec.parameters),
            "num_tests": num_tests,
            "param_count": len(spec.parameters),
        }

        return PromptRenderer.render(template, context)
