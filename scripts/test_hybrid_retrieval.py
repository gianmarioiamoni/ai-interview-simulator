# scripts/test_hybrid_retrieval.py

from services.retrieval.contracts import (
    RetrievalQuery,
)

from services.retrieval.corpus_retrieval_preparator import (
    CorpusRetrievalPreparator,
)

from services.retrieval.semantic_retrieval_engine import (
    SemanticRetrievalEngine,
)

from services.retrieval.embedding_generator import (
    EmbeddingGenerator,
)

from services.retrieval.hybrid_retrieval_fusion_engine import (
    HybridRetrievalFusionEngine,
)


def main() -> None:

    # -------------------------------------------------
    # PREPARE CORPUS
    # -------------------------------------------------

    preparator = CorpusRetrievalPreparator()

    corpus = preparator.prepare(
        corpus_path=("datasets/curated/" "tech_interview_handbook.json")
    )

    # -------------------------------------------------
    # SYMBOLIC RETRIEVAL
    # -------------------------------------------------

    retrieval_engine = SemanticRetrievalEngine()

    query = RetrievalQuery(
        text=("distributed systems " "consistency scaling"),
        required_tags=[
            "distributed_systems",
        ],
        preferred_categories=[
            "distributed_systems",
        ],
        minimum_score=0.4,
        top_k=5,
    )

    symbolic_results = retrieval_engine.retrieve(
        query=query,
        corpus=corpus,
    )

    # -------------------------------------------------
    # EMBEDDINGS
    # -------------------------------------------------

    generator = EmbeddingGenerator()

    embedding_records = generator.generate(corpus)

    # -------------------------------------------------
    # HYBRID FUSION
    # -------------------------------------------------

    fusion_engine = HybridRetrievalFusionEngine()

    fused_results = fusion_engine.fuse(
        query=query.text,
        symbolic_results=(symbolic_results),
        embedding_records=(embedding_records),
    )

    # -------------------------------------------------
    # DIAGNOSTICS
    # -------------------------------------------------

    print()
    print("HYBRID RETRIEVAL")

    print()

    print(f"TOTAL RESULTS: " f"{len(fused_results)}")

    for index, result in enumerate(
        fused_results,
        start=1,
    ):

        symbolic = result.symbolic_result

        print()

        print(f"RESULT #{index}")

        print()

        print(symbolic.record.content)

        print()

        print(f"symbolic_score: " f"{symbolic.final_score}")

        print()

        print(f"embedding_similarity: " f"{result.embedding_similarity}")

        print()

        print(f"semantic_overlap: " f"{symbolic.semantic_overlap}")

        print()

        print(f"fused_score: " f"{result.fused_score}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
