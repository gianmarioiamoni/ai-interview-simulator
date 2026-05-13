# services/question_intelligence/retrieval/retrieval_role_hints.py

from domain.contracts.user.role import (
    RoleType,
)

ROLE_HINTS = {
    RoleType.BACKEND_ENGINEER: [
        "API design",
        "distributed systems",
        "database performance",
        "backend scalability",
        "microservices",
    ],
    RoleType.FRONTEND_ENGINEER: [
        "React",
        "rendering optimization",
        "state management",
        "frontend architecture",
        "browser performance",
    ],
    RoleType.FULLSTACK_ENGINEER: [
        "frontend/backend integration",
        "end-to-end architecture",
        "API communication",
        "fullstack scalability",
        "cross-layer debugging",
    ],
    RoleType.DEVOPS_ENGINEER: [
        "CI/CD",
        "infrastructure as code",
        "observability",
        "Kubernetes",
        "cloud infrastructure",
    ],
    RoleType.DATA_ENGINEER: [
        "data pipelines",
        "ETL systems",
        "distributed processing",
        "data warehousing",
        "streaming systems",
    ],
    RoleType.ML_ENGINEER: [
        "ML pipelines",
        "model deployment",
        "feature engineering",
        "training infrastructure",
        "inference optimization",
    ],
    RoleType.QA_ENGINEER: [
        "test automation",
        "integration testing",
        "quality engineering",
        "test strategy",
        "edge case validation",
    ],
}
