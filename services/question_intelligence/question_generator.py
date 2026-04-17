# services/question_intelligence/question_generator.py

# QuestionGenerator
#
# Responsibility:
# Generates additional interview questions using LLM.
# Enforces strict JSON structure and validates via Pydantic.

import json
from typing import List

from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType

from infrastructure.llm.llm_factory import get_llm


class QuestionGenerator:
    def __init__(self) -> None:
        self._llm = get_llm()

    def generate(
        self,
        role: str,
        level: str,
        interview_type: InterviewType,
        area: InterviewArea,
        n: int = 2,
    ) -> List[GeneratedQuestion]:

        prompt = self._build_prompt(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            n=n,
        )

        response = self._llm.invoke(prompt, temperature=0.7)

        data = json.loads(response.content)

        return [GeneratedQuestion(**item) for item in data]

    def _build_prompt(
        self,
        role: str,
        level: str,
        interview_type: InterviewType,
        area: InterviewArea,
        n: int,
    ) -> str:

        return f"""
            You are an expert technical interviewer.

            Generate {n} {interview_type.value} interview questions
            for a {level} {role} candidate
            in the area of {area.value}.

            IMPORTANT:
             - Questions MUST be diverse and different in topic and structure
             - DO NOT repeat similar questions
             - Each question must be different in topic and structure


            Return STRICTLY a JSON array of objects with:
                - text (string)
                - difficulty (integer 1-5)

            No explanations.
            No markdown.
            Only valid JSON.
        """
