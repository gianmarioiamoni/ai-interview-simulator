# services/question_intelligence/technical_question_filter.py

import re

from services.question_intelligence.quality.contracts import (
    TechnicalFilterResult,
)

class TechnicalQuestionFilter:

    # =====================================================
    # TECHNICAL TAXONOMY
    # =====================================================

    STRONG_BACKEND_TERMS = {
        "microservice",
        "authentication",
        "authorization",
        "jwt",
        "middleware",
        "api gateway",
        "rest api",
        "graphql",
        "backend architecture",
        "service discovery",
        "idempotency",
    }

    WEAK_BACKEND_TERMS = {
        "api",
        "server",
        "endpoint",
        "session",
        "request",
        "response",
    }

    STRONG_DATABASE_TERMS = {
        "sql",
        "transaction",
        "replication",
        "sharding",
        "database",
        "normalization",
        "acid",
        "event sourcing",
        "write amplification",
    }

    WEAK_DATABASE_TERMS = {
        "index",
        "schema",
        "table",
        "consistency",
    }

    STRONG_DISTRIBUTED_TERMS = {
    "distributed systems",
    "eventual consistency",
    "cap theorem",
    "consensus",
    "quorum",
    "leader election",
    "load balancer",
    "rate limiter",
    "fault tolerance",
    "high availability",
    "replication",
    }

    WEAK_DISTRIBUTED_TERMS = {
    "cache",
    "latency",
    "throughput",
    "scaling",
    "partitioning",
    "cdn",
    "failover",
    }

    STRONG_FRONTEND_TERMS = {
    "react",
    "virtual dom",
    "state management",
    "hydration",
    "server side rendering",
    "frontend architecture",
    }

    WEAK_FRONTEND_TERMS = {
    "component",
    "rendering",
    "typescript",
    "javascript",
    "dom",
    }

    STRONG_DEVOPS_TERMS = {
        "kubernetes",
        "terraform",
        "helm",
        "ci/cd",
        "observability",
        "infrastructure as code",
        "container orchestration",
    }

    WEAK_DEVOPS_TERMS = {
        "docker",
        "deployment",
        "pipeline",
        "cloud",
        "monitoring",
    }

    STRONG_DATA_ENGINEERING_TERMS = {
        "etl",
        "stream processing",
        "data warehouse",
        "lakehouse",
        "data pipeline",
        "spark",
        "kafka",
    }

    WEAK_DATA_ENGINEERING_TERMS = {
        "analytics",
        "batch",
        "streaming",
        "warehouse",
    }

    STRONG_ML_TERMS = {
        "transformer",
        "fine tuning",
        "rag",
        "embedding",
        "model serving",
        "feature engineering",
    }

    WEAK_ML_TERMS = {
        "machine learning",
        "training",
        "inference",
        "model",
        "vector",
    }

    STRONG_CS_TERMS = {
        "time complexity",
        "space complexity",
        "binary search",
        "dynamic programming",
        "concurrency",
        "parallelism",
        "deadlock",
    }

    WEAK_CS_TERMS = {
        "algorithm",
        "thread",
        "mutex",
        "hash table",
        "sorting",
    }

    # =====================================================
    # AGGREGATED TAXONOMY
    # =====================================================

    ALL_TERMS = (
        STRONG_BACKEND_TERMS
        | WEAK_BACKEND_TERMS
        | STRONG_DATABASE_TERMS
        | WEAK_DATABASE_TERMS
        | STRONG_DISTRIBUTED_TERMS
        | WEAK_DISTRIBUTED_TERMS
        | STRONG_FRONTEND_TERMS
        | WEAK_FRONTEND_TERMS
        | STRONG_DEVOPS_TERMS
        | WEAK_DEVOPS_TERMS
        | STRONG_DATA_ENGINEERING_TERMS
        | WEAK_DATA_ENGINEERING_TERMS
        | STRONG_ML_TERMS
        | WEAK_ML_TERMS
        | STRONG_CS_TERMS
        | WEAK_CS_TERMS
    )

    # =====================================================
    # PUBLIC
    # =====================================================

    def evaluate(
        self,
        text: str,
    ) -> TechnicalFilterResult:

        normalized = self._normalize_text(text)

        matched_categories = self.matching_categories(normalized)

        matched_terms = [
            term
            for term in self.ALL_TERMS
            if self._contains_term(
                normalized,
                term,
            )
        ]

        # -------------------------------------------------
        # SCORING
        # -------------------------------------------------

        category_score = len(matched_categories) * 0.25

        term_score = min(
            len(matched_terms) * 0.10,
            0.5,
        )

        score = min(
            category_score + term_score,
            1.0,
        )

        return TechnicalFilterResult(
            is_technical=(score >= 0.25),
            score=round(
                score,
                2,
            ),
            matched_categories=(matched_categories),
            matched_terms=(matched_terms),
        )

    def is_technical(
        self,
        text: str,
    ) -> bool:

        result = self.evaluate(
            text
        )

        return (
            result.is_technical
        )

    def matching_categories(
        self,
        text: str,
    ) -> list[str]:

        normalized = text.lower()

        categories: list[str] = []

        taxonomy = {
            "backend": self.STRONG_BACKEND_TERMS | self.WEAK_BACKEND_TERMS,
            "database": self.STRONG_DATABASE_TERMS | self.WEAK_DATABASE_TERMS,
            "distributed_systems": self.STRONG_DISTRIBUTED_TERMS | self.WEAK_DISTRIBUTED_TERMS,
            "frontend": self.STRONG_FRONTEND_TERMS | self.WEAK_FRONTEND_TERMS,
            "devops": self.STRONG_DEVOPS_TERMS | self.WEAK_DEVOPS_TERMS,
            "data_engineering": self.STRONG_DATA_ENGINEERING_TERMS | self.WEAK_DATA_ENGINEERING_TERMS,
            "machine_learning": self.STRONG_ML_TERMS | self.WEAK_ML_TERMS,
            "computer_science": self.STRONG_CS_TERMS | self.WEAK_CS_TERMS,
        }

        for (
            category,
            keywords,
        ) in taxonomy.items():

            matched = any(
                self._contains_term(
                    normalized,
                    keyword,
                )
                for keyword in keywords
            )

            if matched:
                categories.append(category)

        return categories

    # =====================================================
    # HELPERS
    # =====================================================

    def _contains_term(
        self,
        text: str,
        term: str,
    ) -> bool:

        normalized_text = self._normalize_text(text)

        normalized_term = self._normalize_text(term)

        pattern = r"\b" + re.escape(normalized_term) + r"\b"

        return (
            re.search(
                pattern,
                normalized_text,
            )
            is not None
        )

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        normalized = text.lower()

        replacements = {
            "deadlocks": "deadlock",
            "mutexes": "mutex",
            "indexes": "index",
            "queries": "query",
            "pipelines": "pipeline",
            "transactions": "transaction",
            "deployments": "deployment",
            "systems": "system",
        }

        for (
            source,
            target,
        ) in replacements.items():

            normalized = normalized.replace(
                source,
                target,
            )

        return normalized

        
    def _category_matches(
        self,
        normalized_text: str,
        strong_terms: set[str],
        weak_terms: set[str],
    ) -> tuple[bool, list[str], list[str]]:

        normalized_text = self._normalize_text(normalized_text)

        strong_matches = [
            term
            for term in strong_terms
            if self._contains_term(normalized_text, term)
        ]

        weak_matches = [
            term
            for term in weak_terms
            if self._contains_term(normalized_text, term)
        ]

        # -------------------------------------------------
        # MATCH RULES
        # -------------------------------------------------

        is_match = (
            len(strong_matches) >= 1
            or len(weak_matches) >= 2
        )

        return (
            is_match,
            strong_matches,
            weak_matches,
        )
