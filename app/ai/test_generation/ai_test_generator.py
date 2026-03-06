# app/ai/test_generation/ai_test_generator.py

from domain.contracts.test_case import TestCase
from domain.contracts.question import Question

from infrastructure.llm.llm_factory import get_llm


class AITestGenerator:

    def __init__(self):

        self._llm = get_llm()

    def generate_tests(
        self,
        question: Question,
        num_tests: int = 3,
    ) -> list[TestCase]:

        prompt = f"""
Generate {num_tests} edge-case test cases for this coding problem.

Problem:
{question.prompt}

Return JSON array:
[
  {{"input": "...", "expected_output": "..."}}
]
"""

        response = self._llm.invoke(prompt)

        tests_json = response.json()

        return [
            TestCase(
                input=t["input"],
                expected_output=t["expected_output"],
            )
            for t in tests_json
        ]
