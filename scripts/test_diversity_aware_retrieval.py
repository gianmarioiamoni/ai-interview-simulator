# scripts/test_diversity_aware_retrieval.py

from services.retrieval.contracts import (
    HybridRetrievalResult,
    RetrievalCorpusRecord,
    RetrievalResult,
)

from services.retrieval.diversity_aware_reranker import (
    DiversityAwareReranker,
)

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
    NormalizedQuestionRecord,
)

from services.question_ingestion.contracts import (
    IngestionMetadata,
)

def build_result(
    content: str,
    categories: list[str],
    tags: list[str],
    score: float,
) -> RetrievalResult:

    # -------------------------------------------------
    # NORMALIZED QUESTION
    # -------------------------------------------------

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

    # -------------------------------------------------
    # CURATED CORPUS RECORD
    # -------------------------------------------------

    curated = CuratedCorpusRecord(
        question=normalized,
        semantic_score=score,
        matched_categories=categories,
        matched_terms=tags,
        source_repository=("test_repository"),
        onboarding_decision="approved",
        corpus_version="v1",
    )

    # -------------------------------------------------
    # RETRIEVAL CORPUS RECORD
    # -------------------------------------------------

    record = RetrievalCorpusRecord(
        content=content,
        retrieval_tags=tags,
        retrieval_score=score,
        source_repository=("test_repository"),
        corpus_version="v1",
        semantic_categories=categories,
        original_record=curated,
    )

    # -------------------------------------------------
    # RETRIEVAL RESULT
    # -------------------------------------------------

    return RetrievalResult(
        record=record,
        final_score=score,
        matched_tags=tags,
        matched_categories=categories,
        semantic_overlap=0.8,
        is_admissible=True,
    )


def main() -> None:

    results = [
        HybridRetrievalResult(
            symbolic_result=(
                build_result(
                    content=("Distributed cache design"),
                    categories=["distributed_systems"],
                    tags=["cache"],
                    score=1.8,
                )
            ),
            embedding_similarity=0.82,
            fused_score=1.8,
        ),
        HybridRetrievalResult(
            symbolic_result=(
                build_result(
                    content=("Eventual consistency"),
                    categories=["distributed_systems"],
                    tags=["consistency"],
                    score=1.7,
                )
            ),
            embedding_similarity=0.79,
            fused_score=1.7,
        ),
        HybridRetrievalResult(
            symbolic_result=(
                build_result(
                    content=("Database sharding"),
                    categories=["database"],
                    tags=["database"],
                    score=1.6,
                )
            ),
            embedding_similarity=0.70,
            fused_score=1.6,
        ),
    ]

    reranker = DiversityAwareReranker()

    reranked = reranker.rerank(
        results=results,
    )

    print()

    print("DIVERSITY-AWARE RETRIEVAL")

    print()

    for index, result in enumerate(
        reranked,
        start=1,
    ):

        symbolic = result.symbolic_result

        print(f"RESULT #{index}")

        print()

        print(symbolic.record.content)

        print()

        print(f"fused_score: " f"{result.fused_score}")

        print()

        print(f"categories: " f"{symbolic.matched_categories}")

        print()

        print("-" * 80)

        print()


if __name__ == "__main__":

    main()
