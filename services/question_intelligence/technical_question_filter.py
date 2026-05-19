# services/question_intelligence/technical_question_filter.py

import re

from services.question_intelligence.quality.contracts import (
    TechnicalFilterResult,
)

class TechnicalQuestionFilter:

    # =====================================================
    # TECHNICAL TAXONOMY
    # =====================================================

    BACKEND_TERMS = {
        "api",
        "backend",
        "microservice",
        "rest",
        "graphql",
        "authentication",
        "authorization",
        "jwt",
        "session",
        "middleware",
        "server",
    }

    DATABASE_TERMS = {
        "sql",
        "database",
        "query",
        "index",
        "transaction",
        "join",
        "normalization",
        "replication",
        "sharding",
        "oltp",
        "olap",
    }

    DISTRIBUTED_SYSTEMS_TERMS = {
        "distributed",
        "consistency",
        "partition",
        "latency",
        "throughput",
        "scaling",
        "load balancer",
        "rate limiter",
        "caching",
        "cache",
        "cdn",
        "eventual consistency",
        "consensus",
        "cap theorem",
    }

    FRONTEND_TERMS = {
        "react",
        "frontend",
        "rendering",
        "javascript",
        "typescript",
        "component",
        "state management",
        "dom",
        "virtual dom",
    }

    DEVOPS_TERMS = {
        "docker",
        "kubernetes",
        "deployment",
        "ci/cd",
        "pipeline",
        "cloud",
        "terraform",
        "helm",
        "monitoring",
        "observability",
    }

    DATA_ENGINEERING_TERMS = {
        "etl",
        "analytics",
        "data pipeline",
        "streaming",
        "warehouse",
        "lakehouse",
        "spark",
        "kafka",
    }

    ML_TERMS = {
        "machine learning",
        "feature engineering",
        "model serving",
        "training",
        "inference",
        "embedding",
        "rag",
        "transformer",
        "fine tuning",
    }

    COMPUTER_SCIENCE_TERMS = {
        "algorithm",
        "time complexity",
        "space complexity",
        "deadlock",
        "mutex",
        "thread",
        "concurrency",
        "parallelism",
        "memory management",
        "binary search",
        "hash table",
    }

    # =====================================================
    # AGGREGATED TAXONOMY
    # =====================================================

    ALL_TERMS = (
        BACKEND_TERMS
        | DATABASE_TERMS
        | DISTRIBUTED_SYSTEMS_TERMS
        | FRONTEND_TERMS
        | DEVOPS_TERMS
        | DATA_ENGINEERING_TERMS
        | ML_TERMS
        | COMPUTER_SCIENCE_TERMS
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
            "backend": self.BACKEND_TERMS,
            "database": self.DATABASE_TERMS,
            "distributed_systems": (self.DISTRIBUTED_SYSTEMS_TERMS),
            "frontend": self.FRONTEND_TERMS,
            "devops": self.DEVOPS_TERMS,
            "data_engineering": (self.DATA_ENGINEERING_TERMS),
            "machine_learning": self.ML_TERMS,
            "computer_science": (self.COMPUTER_SCIENCE_TERMS),
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
