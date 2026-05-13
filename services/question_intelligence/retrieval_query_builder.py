# services/question_intelligence/retrieval_query_builder.py

import random

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.role import RoleType

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)


class RetrievalQueryBuilder:

    _AREA_HINTS = {
        InterviewArea.TECH_FRONTEND: [
            "React patterns",
            "state management",
            "rendering optimization",
            "component architecture",
            "frontend scalability",
        ],
        InterviewArea.TECH_BACKEND: [
            "API architecture",
            "distributed systems",
            "backend scalability",
            "caching",
            "database performance",
        ],
        InterviewArea.TECH_SYSTEM_DESIGN: [
            "high scalability",
            "distributed systems",
            "microservices",
            "fault tolerance",
            "load balancing",
        ],
        InterviewArea.TECH_DATABASE: [
            "SQL joins",
            "query optimization",
            "indexing",
            "data modeling",
            "aggregation queries",
        ],
        InterviewArea.TECH_CODING: [
            "algorithms",
            "data structures",
            "edge cases",
            "performance optimization",
            "problem solving",
        ],
        InterviewArea.BEHAVIORAL: [
            "team collaboration",
            "conflict resolution",
            "leadership",
            "ownership",
            "communication",
        ],
    }

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
    ) -> str:

        area_hints = self._AREA_HINTS.get(
            area,
            [],
        )

        sampled_hints = random.sample(
            area_hints,
            min(3, len(area_hints)),
        )

        hints_text = ", ".join(sampled_hints)

        return f"""
You are retrieving high-quality interview questions.

Candidate profile:
- Role: {role.value}
- Seniority: {level.value}
- Area: {area.value}

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
