# scripts/test_semantic_retrieval.py

from services.retrieval.corpus_retrieval_preparator import (
    CorpusRetrievalPreparator,
)

from services.retrieval.semantic_retrieval_engine import (
    SemanticRetrievalEngine,
)

from services.retrieval.contracts import (
    RetrievalQuery,
)


def main() -> None:

    preparator = CorpusRetrievalPreparator()

    corpus = preparator.prepare(
        corpus_path=("datasets/curated/" "tech_interview_handbook.json")
    )

    engine = SemanticRetrievalEngine()

    query = RetrievalQuery(
        text=("distributed systems " "consistency cache"),
        required_tags=[
            "distributed_systems",
        ],
        preferred_categories=[
            "distributed_systems",
        ],
        minimum_score=0.4,
        top_k=3,
    )

    results = engine.retrieve(
        query=query,
        corpus=corpus,
    )

    print()
    print("SEMANTIC RETRIEVAL")

    print()

    print(f"TOTAL RESULTS: " f"{len(results)}")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(f"RESULT #{index}")

        print()

        print(result.record.content)

        print()

        print(f"final_score: " f"{result.final_score}")

        print()

        print(f"matched_tags: " f"{result.matched_tags}")

        print()

        print(f"matched_categories: " f"{result.matched_categories}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
