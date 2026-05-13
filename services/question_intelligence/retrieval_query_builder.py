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

    # =====================================================
    # HR
    # =====================================================

    InterviewArea.HR_BACKGROUND: [
        "career growth",
        "past experience",
        "technical ownership",
        "project challenges",
        "professional achievements",
    ],

    InterviewArea.HR_TECHNICAL_KNOWLEDGE: [
        "technical communication",
        "technology decisions",
        "engineering practices",
        "cross-functional collaboration",
        "technical trade-offs",
    ],

    InterviewArea.HR_SITUATIONAL: [
        "conflict resolution",
        "team collaboration",
        "leadership",
        "stakeholder management",
        "difficult situations",
    ],

    InterviewArea.HR_BRAIN_TEASER: [
        "logical reasoning",
        "problem decomposition",
        "creative thinking",
        "analytical thinking",
        "edge-case reasoning",
    ],

    InterviewArea.HR_ANALYTICAL: [
        "data-driven thinking",
        "root cause analysis",
        "decision making",
        "critical thinking",
        "structured reasoning",
    ],

    # =====================================================
    # TECHNICAL
    # =====================================================

    InterviewArea.TECH_BACKGROUND: [
        "past architecture decisions",
        "production experience",
        "scalability challenges",
        "technical ownership",
        "system evolution",
    ],

    InterviewArea.TECH_TECHNICAL_KNOWLEDGE: [
        "backend architecture",
        "frontend architecture",
        "API design",
        "performance optimization",
        "engineering best practices",
    ],

    InterviewArea.TECH_CASE_STUDY: [
        "distributed systems",
        "system scalability",
        "microservices",
        "fault tolerance",
        "high availability",
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
    ]}

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
