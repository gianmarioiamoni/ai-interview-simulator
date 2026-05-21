# scripts/test_memory_aware_retrieval_pipeline.py

from services.retrieval.contracts import (
    HybridRetrievalResult,
    RetrievalCorpusRecord,
    RetrievalResult,
)

from services.retrieval.memory_aware_retrieval_pipeline import (
    MemoryAwareRetrievalPipeline,
)

from services.retrieval.retrieval_session_memory import (
    RetrievalSessionMemory,
)

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
    IngestionMetadata,
    NormalizedQuestionRecord,
)


def build_result(
    content: str,
    categories: list[str],
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
        matched_categories=categories,
        matched_terms=["test"],
        source_repository=("test_repository"),
        onboarding_decision=("approved"),
        corpus_version="v1",
    )

    retrieval_record = RetrievalCorpusRecord(
        content=content,
        retrieval_tags=["test"],
        retrieval_score=score,
        source_repository=("test_repository"),
        corpus_version="v1",
        semantic_categories=categories,
        original_record=curated,
    )

    retrieval_result = RetrievalResult(
        record=retrieval_record,
        final_score=score,
        matched_tags=["test"],
        matched_categories=categories,
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

    # -------------------------------------------------
    # PREVIOUS EXPOSURE
    # -------------------------------------------------

    memory.remember("How would you design " "a distributed cache?")

    # -------------------------------------------------
    # INPUT RESULTS
    # -------------------------------------------------

    results = [
        build_result(
            content=("How would you architect " "a distributed caching layer?"),
            categories=["distributed_systems"],
            score=1.8,
        ),
        build_result(
            content=("Explain database " "sharding strategies."),
            categories=["database"],
            score=1.7,
        ),
        build_result(
            content=("Explain eventual " "consistency trade-offs."),
            categories=["distributed_systems"],
            score=1.6,
        ),
    ]

    pipeline = MemoryAwareRetrievalPipeline(
        memory=memory,
    )

    final_results = pipeline.process(results)

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("MEMORY-AWARE RETRIEVAL PIPELINE")

    print()

    for index, result in enumerate(
        final_results,
        start=1,
    ):

        print(f"RESULT #{index}")

        print()

        print(result.symbolic_result.record.content)

        print()

        print(f"fused_score: " f"{result.fused_score}")

        print()

        print(f"categories: " f"{result.symbolic_result.matched_categories}")

        print()

        print("-" * 80)

        print()

    # -------------------------------------------------
    # MEMORY STATE
    # -------------------------------------------------

    print()

    print("UPDATED MEMORY")

    print()

    for question in memory.get_recent_questions():

        print(question)


if __name__ == "__main__":
    main()
