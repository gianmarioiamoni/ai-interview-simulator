# services/explanation/test_case_explanation_service.py

from typing import Optional

from infrastructure.llm.llm_factory import get_llm


class TestCaseExplanationService:

    def __init__(self):
        self._llm = get_llm()

    def explain(
        self,
        input_data,
        expected,
        actual,
    ) -> Optional[str]:

        prompt = self._build_prompt(input_data, expected, actual)

        try:
            response = self._llm.invoke(prompt)
            content = response.content.strip()

            if not content:
                return None

            return content

        except Exception:
            return None

    # =========================================================

    def _build_prompt(self, input_data, expected, actual) -> str:

        return f"""
You are a senior Python engineer helping debug a coding problem.

INPUT:
{input_data}

EXPECTED OUTPUT:
{expected}

ACTUAL OUTPUT:
{actual}

TASK:
Explain the most likely cause of the incorrect result.

RULES:
- One short sentence
- No code
- No generic advice
- Be specific

OUTPUT:
A single sentence explanation.
"""
