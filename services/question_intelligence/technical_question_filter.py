# services/question_intelligence/technical_question_filter.py

import re

from services.question_intelligence.quality.contracts import TechnicalFilterResult


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
        "query",
        "consistency",
    }

    STRONG_DISTRIBUTED_TERMS = {
        "distributed system",
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
    # CATEGORY MAP
    # =====================================================

    CATEGORY_MAP = {
        "backend": (
            STRONG_BACKEND_TERMS,
            WEAK_BACKEND_TERMS,
        ),
        "database": (
            STRONG_DATABASE_TERMS,
            WEAK_DATABASE_TERMS,
        ),
        "distributed_systems": (
            STRONG_DISTRIBUTED_TERMS,
            WEAK_DISTRIBUTED_TERMS,
        ),
        "frontend": (
            STRONG_FRONTEND_TERMS,
            WEAK_FRONTEND_TERMS,
        ),
        "devops": (
            STRONG_DEVOPS_TERMS,
            WEAK_DEVOPS_TERMS,
        ),
        "data_engineering": (
            STRONG_DATA_ENGINEERING_TERMS,
            WEAK_DATA_ENGINEERING_TERMS,
        ),
        "machine_learning": (
            STRONG_ML_TERMS,
            WEAK_ML_TERMS,
        ),
        "computer_science": (
            STRONG_CS_TERMS,
            WEAK_CS_TERMS,
        ),
    }

    # =====================================================
    # PUBLIC
    # =====================================================

    def evaluate(
        self,
        text: str,
    ) -> TechnicalFilterResult:

        normalized = self._normalize_text(text)

        matched_categories: list[str] = []

        matched_terms: list[str] = []

        score = 0.0

        # -------------------------------------------------
        # CATEGORY MATCHING
        # -------------------------------------------------

        for (
            category,
            (
                strong_terms,
                weak_terms,
            ),
        ) in self.CATEGORY_MAP.items():

            (
                is_match,
                strong_matches,
                weak_matches,
            ) = self._category_matches(
                normalized_text=normalized,
                strong_terms=strong_terms,
                weak_terms=weak_terms,
            )

            if not is_match:
                continue

            matched_categories.append(category)

            matched_terms.extend(strong_matches)
            matched_terms.extend(weak_matches)

            # -------------------------------------------------
            # WEIGHTED SCORING
            # -------------------------------------------------

            score += len(strong_matches) * 0.25
            score += len(weak_matches) * 0.08

        # -------------------------------------------------
        # MULTI-DOMAIN BONUS
        # -------------------------------------------------

        if len(matched_categories) >= 2:
            score += 0.15

        if len(matched_categories) >= 3:
            score += 0.10

        # -------------------------------------------------
        # FINAL NORMALIZATION
        # -------------------------------------------------

        score = min(score, 1.0)

        matched_terms = sorted(list(set(matched_terms)))

        matched_categories = sorted(list(set(matched_categories)))

        return TechnicalFilterResult(
            is_technical=(score >= 0.30),
            score=round(score, 2),
            matched_categories=matched_categories,
            matched_terms=matched_terms,
        )

    def is_technical(
        self,
        text: str,
    ) -> bool:

        result = self.evaluate(text)

        return result.is_technical

    def matching_categories(
        self,
        text: str,
    ) -> list[str]:

        normalized = self._normalize_text(text)

        categories: list[str] = []

        for (
            category,
            (
                strong_terms,
                weak_terms,
            ),
        ) in self.CATEGORY_MAP.items():

            (
                is_match,
                _strong,
                _weak,
            ) = self._category_matches(
                normalized_text=normalized,
                strong_terms=strong_terms,
                weak_terms=weak_terms,
            )

            if is_match:
                categories.append(category)

        return categories

    # =====================================================
    # HELPERS
    # =====================================================

    def _category_matches(
        self,
        normalized_text: str,
        strong_terms: set[str],
        weak_terms: set[str],
    ) -> tuple[bool, list[str], list[str]]:

        strong_matches = [
            term
            for term in strong_terms
            if self._contains_term(
                normalized_text,
                term,
            )
        ]

        weak_matches = [
            term
            for term in weak_terms
            if self._contains_term(
                normalized_text,
                term,
            )
        ]

        # -------------------------------------------------
        # MATCH RULES
        # -------------------------------------------------

        is_match = len(strong_matches) >= 1 or len(weak_matches) >= 2

        return (
            is_match,
            strong_matches,
            weak_matches,
        )

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
            "services": "service",
            "servers": "server",
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
