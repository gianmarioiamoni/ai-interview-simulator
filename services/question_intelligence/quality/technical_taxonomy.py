# services/question_intelligence/quality/technical_taxonomy.py


class TechnicalTaxonomy:
    """
    Static taxonomy of technical terms organised by category and signal strength.

    Each category maps to a tuple of (strong_terms, weak_terms).
    Strong terms carry higher scoring weight; weak terms require at least two
    matches to qualify a text as belonging to the category.
    """

    STRONG_BACKEND_TERMS: frozenset[str] = frozenset(
        {
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
    )

    WEAK_BACKEND_TERMS: frozenset[str] = frozenset(
        {
            "api",
            "server",
            "endpoint",
            "session",
            "request",
            "response",
        }
    )

    STRONG_DATABASE_TERMS: frozenset[str] = frozenset(
        {
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
    )

    WEAK_DATABASE_TERMS: frozenset[str] = frozenset(
        {
            "index",
            "schema",
            "table",
            "query",
            "consistency",
        }
    )

    STRONG_DISTRIBUTED_TERMS: frozenset[str] = frozenset(
        {
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
    )

    WEAK_DISTRIBUTED_TERMS: frozenset[str] = frozenset(
        {
            "cache",
            "latency",
            "throughput",
            "scaling",
            "partitioning",
            "cdn",
            "failover",
        }
    )

    STRONG_FRONTEND_TERMS: frozenset[str] = frozenset(
        {
            "react",
            "virtual dom",
            "state management",
            "hydration",
            "server side rendering",
            "frontend architecture",
        }
    )

    WEAK_FRONTEND_TERMS: frozenset[str] = frozenset(
        {
            "component",
            "rendering",
            "typescript",
            "javascript",
            "dom",
        }
    )

    STRONG_DEVOPS_TERMS: frozenset[str] = frozenset(
        {
            "kubernetes",
            "terraform",
            "helm",
            "ci/cd",
            "observability",
            "infrastructure as code",
            "container orchestration",
        }
    )

    WEAK_DEVOPS_TERMS: frozenset[str] = frozenset(
        {
            "docker",
            "deployment",
            "pipeline",
            "cloud",
            "monitoring",
        }
    )

    STRONG_DATA_ENGINEERING_TERMS: frozenset[str] = frozenset(
        {
            "etl",
            "stream processing",
            "data warehouse",
            "lakehouse",
            "data pipeline",
            "spark",
            "kafka",
        }
    )

    WEAK_DATA_ENGINEERING_TERMS: frozenset[str] = frozenset(
        {
            "analytics",
            "batch",
            "streaming",
            "warehouse",
        }
    )

    STRONG_ML_TERMS: frozenset[str] = frozenset(
        {
            "transformer",
            "fine tuning",
            "rag",
            "embedding",
            "model serving",
            "feature engineering",
        }
    )

    WEAK_ML_TERMS: frozenset[str] = frozenset(
        {
            "machine learning",
            "training",
            "inference",
            "model",
            "vector",
        }
    )

    STRONG_CS_TERMS: frozenset[str] = frozenset(
        {
            "time complexity",
            "space complexity",
            "binary search",
            "dynamic programming",
            "concurrency",
            "parallelism",
            "deadlock",
        }
    )

    WEAK_CS_TERMS: frozenset[str] = frozenset(
        {
            "algorithm",
            "thread",
            "mutex",
            "hash table",
            "sorting",
        }
    )

    CATEGORY_MAP: dict[str, tuple[frozenset[str], frozenset[str]]] = {
        "backend": (STRONG_BACKEND_TERMS, WEAK_BACKEND_TERMS),
        "database": (STRONG_DATABASE_TERMS, WEAK_DATABASE_TERMS),
        "distributed_systems": (STRONG_DISTRIBUTED_TERMS, WEAK_DISTRIBUTED_TERMS),
        "frontend": (STRONG_FRONTEND_TERMS, WEAK_FRONTEND_TERMS),
        "devops": (STRONG_DEVOPS_TERMS, WEAK_DEVOPS_TERMS),
        "data_engineering": (STRONG_DATA_ENGINEERING_TERMS, WEAK_DATA_ENGINEERING_TERMS),
        "machine_learning": (STRONG_ML_TERMS, WEAK_ML_TERMS),
        "computer_science": (STRONG_CS_TERMS, WEAK_CS_TERMS),
    }
