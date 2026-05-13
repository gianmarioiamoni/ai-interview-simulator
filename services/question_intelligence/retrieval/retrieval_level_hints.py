# services/question_intelligence/retrieval/retrieval_level_hints.py

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

LEVEL_HINTS = {
    SeniorityLevel.JUNIOR: [
        "fundamentals",
        "basic implementation",
        "debugging",
        "simple architecture",
        "learning mindset",
    ],
    SeniorityLevel.MID: [
        "production experience",
        "best practices",
        "scalability awareness",
        "trade-offs",
        "real-world scenarios",
    ],
    SeniorityLevel.SENIOR: [
        "system design",
        "technical leadership",
        "architecture decisions",
        "distributed systems",
        "high scalability",
    ],
}
