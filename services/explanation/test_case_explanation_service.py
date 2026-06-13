# services/explanation/test_case_explanation_service.py

from typing import Optional

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import TESTCASE_EXPLANATION


class TestCaseExplanationService:

    def __init__(self, llm: LLMPort):
        self._llm = llm

    def explain(
        self,
        input_data,
        expected,
        actual,
    ) -> Optional[str]:

        prompt = self._build_prompt(input_data, expected, actual)

        try:
            with LLMOperationContext.scope(TESTCASE_EXPLANATION):
                response = self._llm.invoke(prompt)
            content = response.content.strip()

            if not content:
                return None

            return content

        except Exception:
            return None

    # =========================================================

    def _build_prompt(self, input_data, expected, actual) -> str:

        template = PromptLoader.load("feedback/test_case_explanation.txt")

        return PromptRenderer.render(
            template,
            {
                "input_data": input_data,
                "expected": expected,
                "actual": actual,
            },
        )
