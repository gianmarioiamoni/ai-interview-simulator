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

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION


class QuestionGenerator:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        n: int = 2,
        theme_guidance: str | None = None,
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
            theme_guidance=theme_guidance,
        )

        with LLMOperationContext.scope(QUESTION_GENERATION):
            response = self._llm.invoke(prompt)
        
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
        theme_guidance: str | None = None,
    ) -> str:

        theme_block = ""

        if theme_guidance:
            theme_block = f"\nTHEME GUIDANCE:\n{theme_guidance}\n"

        template = PromptLoader.load("generation/question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "interview_type": interview_type.value,
                "level": level.value,
                "role": role.value,
                "area": area.value,
                "variation": variation,
                "theme_block": theme_block,
            },
        )
