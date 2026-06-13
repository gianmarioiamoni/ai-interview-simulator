# app/ai/test_generation/ai_test_generator.py

from typing import List

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.question.question import Question

from app.ports.llm_port import LLMPort
from infrastructure.config.settings import settings
from app.ai.test_generation.test_prompt_builder import TestPromptBuilder
from app.ai.test_generation.test_response_parser import TestResponseParser
from app.ai.test_generation.test_cache_service import TestCacheService
from app.ai.test_generation.test_diversity_filter import TestDiversityFilter
from app.core.logger import get_logger

logger = get_logger(__name__)


class AITestGenerator:
    """
    Facade that coordinates AI-driven test case generation.

    Delegates prompt construction to TestPromptBuilder and
    LLM invocation + parsing to TestResponseParser, mirroring
    the architecture of SQLQuestionGenerator and CodingQuestionGenerator.
    """

    def __init__(self, llm: LLMPort) -> None:
        self._prompt_builder = TestPromptBuilder()
        self._response_parser = TestResponseParser(llm)
        self._cache = TestCacheService()
        self._diversity_filter = TestDiversityFilter()

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
    ) -> List[CodingTestCase]:

        if not question.coding_spec:
            raise ValueError("CodingSpec required for test generation")

        cached = self._cache.get_tests(question, num_tests)
        if cached:
            return cached

        spec = question.coding_spec
        tests: List[CodingTestCase] = []

        _max_attempts = settings.test_generation_retry_attempts
        for attempt in range(_max_attempts):
            prompt = self._prompt_builder.build(
                problem=question.prompt,
                spec=spec,
                num_tests=num_tests * 2,
            )
            tests = self._response_parser.invoke_and_parse(
                prompt=prompt,
                spec=spec,
                retry=(attempt == _max_attempts - 1),
            )

            if tests:
                break

            logger.warning("test_generation_empty_attempt_%s", attempt)

        if not tests:
            logger.warning("LLM test generation failed → using fallback")
            tests = self._fallback_tests(spec)

        tests = self._diversity_filter.filter(tests, num_tests)
        self._cache.store_tests(question, num_tests, tests)

        return tests

    # ------------------------------------------------------------------
    # FALLBACK
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_tests(spec) -> List[CodingTestCase]:
        num_params = len(spec.parameters)
        base_args = [0] * num_params
        return [
            CodingTestCase(args=base_args, expected=0),
            CodingTestCase(args=[1] * num_params, expected=1),
        ]
