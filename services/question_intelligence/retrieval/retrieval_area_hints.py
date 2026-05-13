# services/question_intelligence/retrieval/retrieval_area_hints.py

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

AREA_HINTS = {
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
    # TECH
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
    ],
}
