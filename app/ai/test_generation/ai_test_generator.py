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
from app.ai.test_generation.oracle_validator import OracleValidator
from app.core.logger import get_logger

logger = get_logger(__name__)


class AITestGenerator:
    """
    Facade that coordinates AI-driven test case generation.

    Delegates prompt construction to TestPromptBuilder and
    LLM invocation + parsing to TestResponseParser, mirroring
    the architecture of SQLQuestionGenerator and CodingQuestionGenerator.

    Oracle validation (R5.2):
    - Reference solution is executed against visible tests (trust check).
    - If trusted, hidden tests with wrong expected values are discarded.
    - Hidden tests whose args overlap with visible tests but disagree on
      expected are also discarded (overlap cross-check).
    """

    def __init__(self, llm: LLMPort) -> None:
        self._prompt_builder = TestPromptBuilder()
        self._response_parser = TestResponseParser(llm)
        self._cache = TestCacheService()
        self._diversity_filter = TestDiversityFilter()
        self._oracle_validator = OracleValidator()

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
        domain_profile=None,
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
                domain_profile=domain_profile,
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
            logger.warning(
                "LLM test generation failed → no hidden tests (visible-only scoring)"
            )
            return []

        # ----------------------------------------------------------
        # R5.2 ORACLE VALIDATION
        # ----------------------------------------------------------
        reference_solution = getattr(question, "reference_solution", None) or ""
        visible_tests = list(getattr(question, "visible_tests", None) or [])
        validated = self._oracle_validator.validate(
            reference_solution=reference_solution,
            entrypoint=spec.entrypoint,
            visible_tests=visible_tests,
            hidden_tests=tests,
        )

        if validated is None:
            # Reference solution missing or not trusted: discard all hidden tests.
            logger.warning(
                "[AITestGenerator] Oracle validation skipped — discarding hidden tests "
                "(visible-only scoring)"
            )
            return []
        elif not validated:
            # All hidden tests discarded by oracle: visible-only scoring.
            logger.warning(
                "[AITestGenerator] All hidden tests discarded by oracle validation "
                "→ visible-only scoring"
            )
            return []
        else:
            tests = validated

        tests = self._diversity_filter.filter(tests, num_tests)
        self._cache.store_tests(question, num_tests, tests)

        return tests
