# services/question_intelligence/question_generator.py

# QuestionGenerator
#
# Responsibility:
# Generates additional interview questions using LLM.
# Enforces strict JSON structure and validates via Pydantic.

import json
from typing import List

from domain.contracts.generated_question import GeneratedQuestion
from infrastructure.llm.llm_factory import get_llm


class QuestionGenerator:
    def __init__(self) -> None:
        self._llm = get_llm()

    def generate(
        self,
        role: str,
        level: str,
        interview_type: str,
        area: str,
        n: int = 2,
    ) -> List[GeneratedQuestion]:

        prompt = self._build_prompt(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            n=n,
        )

        response = self._llm.invoke(prompt)

        data = json.loads(response.content)

        return [GeneratedQuestion(**item) for item in data]

    def _build_prompt(
        self,
        role: str,
        level: str,
        interview_type: str,
        area: str,
        n: int,
    ) -> str:

        return f"""
            You are an expert technical interviewer.

            Generate {n} {interview_type} interview questions
            for a {level} {role} candidate
            in the area of {area}.

            Return STRICTLY a JSON array of objects with:
                - text (string)
                - difficulty (integer 1-5)

            No explanations.
            No markdown.
            Only valid JSON.
        """
