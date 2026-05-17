# services/question_intelligence/retrieval/retrieval_role_hints.py

from domain.contracts.user.role import (
    RoleType,
)


ROLE_HINTS = {
    # =====================================================
    # BACKEND
    # =====================================================
    RoleType.BACKEND_ENGINEER: [
        "backend",
        "api",
        "rest",
        "graphql",
        "database",
        "sql",
        "query",
        "indexing",
        "transactions",
        "connection pooling",
        "microservices",
        "distributed systems",
        "eventual consistency",
        "caching",
        "redis",
        "message queues",
        "rate limiting",
        "authentication",
        "authorization",
        "scalability",
        "load balancing",
        "websocket",
        "server",
    ],
    # =====================================================
    # FRONTEND
    # =====================================================
    RoleType.FRONTEND_ENGINEER: [
        "frontend",
        "react",
        "hooks",
        "reconciliation",
        "rendering",
        "ui",
        "ux",
        "component",
        "state management",
        "memoization",
        "css",
        "browser",
        "dom",
        "javascript",
        "typescript",
        "client-side",
        "server-side rendering",
    ],
    # =====================================================
    # FULLSTACK
    # =====================================================
    RoleType.FULLSTACK_ENGINEER: [
        "fullstack",
        "web application",
        "authentication",
        "api",
        "frontend",
        "backend",
        "database",
        "deployment",
        "integration",
        "architecture",
    ],
    # =====================================================
    # DEVOPS
    # =====================================================
    RoleType.DEVOPS_ENGINEER: [
        "docker",
        "kubernetes",
        "deployment",
        "ci/cd",
        "pipeline",
        "infrastructure",
        "terraform",
        "monitoring",
        "observability",
        "container",
        "orchestration",
        "cloud",
        "load balancing",
        "autoscaling",
        "devops",
    ],
    # =====================================================
    # DATA
    # =====================================================
    RoleType.DATA_ENGINEER: [
        "etl",
        "data pipeline",
        "data warehouse",
        "spark",
        "hadoop",
        "batch processing",
        "streaming",
        "data modeling",
        "aggregation",
        "analytics",
        "big data",
    ],
    # =====================================================
    # ML
    # =====================================================
    RoleType.ML_ENGINEER: [
        "machine learning",
        "ml",
        "training",
        "inference",
        "model serving",
        "feature engineering",
        "embeddings",
        "neural network",
        "llm",
        "rag",
        "vector database",
        "fine-tuning",
    ],
    # =====================================================
    # QA
    # =====================================================
    RoleType.QA_ENGINEER: [
        "testing",
        "qa",
        "test automation",
        "integration testing",
        "unit testing",
        "e2e",
        "selenium",
        "cypress",
        "playwright",
        "quality assurance",
        "regression testing",
    ],
}
