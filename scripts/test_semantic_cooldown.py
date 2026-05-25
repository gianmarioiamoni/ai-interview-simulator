# scripts/test_semantic_cooldown.py

from services.retrieval.contracts import (
    HybridRetrievalResult,
    RetrievalCorpusRecord,
    RetrievalResult,
)
from services.retrieval.retrieval_session_memory import RetrievalSessionMemory
from services.retrieval.semantic_cooldown_reranker import SemanticCooldownReranker
from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
    IngestionMetadata,
    NormalizedQuestionRecord,
)


def build_result(
    content: str,
    score: float,
) -> HybridRetrievalResult:

    normalized = NormalizedQuestionRecord(
        text=content,
        source="test_source",
        ingestion_metadata=(
            IngestionMetadata(
                source_name=("test_repository"),
                source_type="test",
                dataset_version="v1",
                ingestion_timestamp=("2026-01-01T00:00:00Z"),
            )
        ),
    )

    curated = CuratedCorpusRecord(
        question=normalized,
        semantic_score=score,
        matched_categories=["distributed_systems"],
        matched_terms=["cache"],
        source_repository=("test_repository"),
        onboarding_decision=("approved"),
        corpus_version="v1",
    )

    retrieval_record = RetrievalCorpusRecord(
        content=content,
        retrieval_tags=["cache"],
        retrieval_score=score,
        source_repository=("test_repository"),
        corpus_version="v1",
        semantic_categories=["distributed_systems"],
        original_record=curated,
    )

    retrieval_result = RetrievalResult(
        record=retrieval_record,
        final_score=score,
        matched_tags=["cache"],
        matched_categories=["distributed_systems"],
        semantic_overlap=0.8,
        is_admissible=True,
    )

    return HybridRetrievalResult(
        symbolic_result=(retrieval_result),
        embedding_similarity=0.8,
        fused_score=score,
    )


def main() -> None:

    memory = RetrievalSessionMemory()

    memory.remember("How would you design " "a distributed cache?")

    results = [
        build_result(
            content=("How would you architect " "a distributed caching layer?"),
            score=1.8,
        ),
        build_result(
            content=("Explain database " "sharding strategies."),
            score=1.7,
        ),
    ]

    reranker = SemanticCooldownReranker(
        memory=memory,
    )

    adjusted = reranker.rerank(results)

    print()

    print("SEMANTIC COOLDOWN")

    print()

    for index, result in enumerate(
        adjusted,
        start=1,
    ):

        print(f"RESULT #{index}")

        print()

        print(result.symbolic_result.record.content)

        print()

        print(f"fused_score: " f"{result.fused_score}")

        print()

        print("-" * 80)

        print()


if __name__ == "__main__":

    main()
