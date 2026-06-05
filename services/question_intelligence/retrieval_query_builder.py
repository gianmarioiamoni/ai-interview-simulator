# services/question_intelligence/retrieval_query_builder.py

import random

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.retrieval.retrieval_area_hints import (
    AREA_HINTS,
)

from services.question_intelligence.retrieval.retrieval_role_hints import (
    ROLE_HINTS,
)

from services.question_intelligence.retrieval.retrieval_level_hints import (
    LEVEL_HINTS,
)

class RetrievalQueryBuilder:


    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        theme_anchor: str | None = None,
    ) -> str:

        area_hints = AREA_HINTS.get(
            area,
            [],
        )

        role_hints = ROLE_HINTS.get(
            role,
            [],
        )

        level_hints = LEVEL_HINTS.get(
            level,
            [],
        )

        combined_hints = area_hints + role_hints + level_hints

        sampled_hints = random.sample(
            combined_hints,
            min(5, len(combined_hints)),
        )

        hints_text = ", ".join(sampled_hints)

        theme_line = ""

        if theme_anchor:
            readable_theme = theme_anchor.replace("_", " ")
            theme_line = (
                f"\nSoft interview theme anchor: {readable_theme}\n"
                "- prefer naturally related candidates when quality is comparable\n"
            )

        return f"""
You are retrieving high-quality interview questions.

Candidate profile:
- Role: {role.value}
- Seniority: {level.value}
- Area: {area.value}
{theme_line}
Retrieval goals:
- maximize conceptual diversity
- avoid repetitive questions
- prioritize realistic interview scenarios
- prefer production-oriented discussions
- avoid trivia questions

Focus topics:
{hints_text}

Desired properties:
- different problem types
- different reasoning patterns
- non-overlapping concepts
- practical engineering relevance
"""
