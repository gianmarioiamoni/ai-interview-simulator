# services/question_intelligence/retrieval/retrieval_area_hints.py

from domain.contracts.interview.interview_area import (
    InterviewArea,
)


AREA_HINTS = {
    # =====================================================
    # TECHNICAL KNOWLEDGE
    # =====================================================
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE: [
        "rest",
        "graphql",
        "react",
        "hooks",
        "reconciliation",
        "docker",
        "kubernetes",
        "authentication",
        "authorization",
        "ci/cd",
        "websocket",
        "redis",
        "microservices",
        "eventual consistency",
        "cap theorem",
        "message queues",
        "api versioning",
        "cdn",
        "rate limiting",
        "memoization",
    ],
    # =====================================================
    # DATABASE
    # =====================================================
    InterviewArea.TECH_DATABASE: [
        "sql",
        "database",
        "indexing",
        "query optimization",
        "joins",
        "transactions",
        "aggregation",
        "normalization",
        "sharding",
        "connection pooling",
        "locking",
        "distributed transactions",
        "query performance",
        "data modeling",
    ],
    # =====================================================
    # CASE STUDY
    # =====================================================
    InterviewArea.TECH_CASE_STUDY: [
        "design",
        "scalable",
        "architecture",
        "system design",
        "chat application",
        "url shortener",
        "notification system",
        "load balancing",
        "horizontal scaling",
        "distributed systems",
        "production systems",
        "real-world scenario",
    ],
    # =====================================================
    # CODING
    # =====================================================
    InterviewArea.TECH_CODING: [
        "algorithm",
        "coding",
        "implementation",
        "function",
        "complexity",
        "leetcode",
        "problem solving",
        "optimization",
    ],
}
