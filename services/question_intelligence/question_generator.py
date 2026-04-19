# services/question_intelligence/question_generator.py

# QuestionGenerator
#
# Responsibility:
# Generates additional interview questions using LLM.
# Enforces strict JSON structure and validates via Pydantic.

import json
import random

from typing import List

from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from infrastructure.llm.llm_factory import get_llm


class QuestionGenerator:
    def __init__(self) -> None:
        self._llm = get_llm()

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        n: int = 2,
    ) -> List[GeneratedQuestion]:

        VARIATION_SEEDS = [
            "Focus on scalability aspects",
            "Focus on performance trade-offs",
            "Focus on edge cases and failure scenarios",
            "Focus on real-world production issues",
            "Focus on architectural decisions",
        ]

        variation = random.choice(VARIATION_SEEDS)
        prompt = self._build_prompt(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            n=n,
            variation=variation,
        )

        response = self._llm.invoke(prompt, temperature=0.7)

        data = json.loads(response.content)

        return [GeneratedQuestion(**item) for item in data]

    def _build_prompt(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        n: int,
        variation: str,
    ) -> str:

        return f"""
            You are an expert technical interviewer.

            Generate {n} {interview_type.value} interview questions
            for a {level.value} {role.value} candidate
            in the area of {area.value}.

            IMPORTANT:
             - Questions MUST be diverse and different in topic and structure
             - DO NOT repeat similar questions
             - Each question must be different in topic and structure

            CONTEXT:
            {variation}

            Return STRICTLY a JSON array of objects with:
                - text (string)
                - difficulty (integer 1-5)

            No explanations.
            No markdown.
            Only valid JSON.
        """
