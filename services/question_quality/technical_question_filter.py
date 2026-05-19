# services/question_quality/technical_question_filter.py


class TechnicalQuestionFilter:

    # =====================================================
    # CONSTANTS
    # =====================================================

    TECH_KEYWORDS = {
        # backend
        "api",
        "database",
        "sql",
        "transaction",
        "index",
        "query",
        "backend",
        "microservice",
        "cache",
        "caching",
        # distributed systems
        "distributed",
        "replication",
        "partition",
        "consistency",
        "sharding",
        "load balancer",
        "rate limiter",
        "scaling",
        "latency",
        "throughput",
        # frontend
        "react",
        "frontend",
        "rendering",
        "javascript",
        "typescript",
        # devops
        "docker",
        "kubernetes",
        "ci/cd",
        "deployment",
        "cloud",
        "pipeline",
        # data
        "etl",
        "analytics",
        "data pipeline",
        # ml
        "machine learning",
        "feature engineering",
        "model serving",
        # generic engineering
        "system design",
        "architecture",
        "performance",
        "optimization",
    }

    # =====================================================
    # PUBLIC
    # =====================================================

    def is_technical(
        self,
        text: str,
    ) -> bool:

        normalized = text.lower()

        return any(keyword in normalized for keyword in (self.TECH_KEYWORDS))
