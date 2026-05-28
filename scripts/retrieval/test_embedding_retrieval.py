# scripts/test_embedding_retrieval.py

from services.retrieval.corpus_retrieval_preparator import (
    CorpusRetrievalPreparator,
)

from services.retrieval.embedding_generator import (
    EmbeddingGenerator,
)

from services.retrieval.embedding_similarity_engine import (
    EmbeddingSimilarityEngine,
)


def main() -> None:

    preparator = CorpusRetrievalPreparator()

    retrieval_records = preparator.prepare(
        corpus_path=("datasets/curated/" "tech_interview_handbook.json")
    )

    generator = EmbeddingGenerator()

    embedding_records = generator.generate(retrieval_records)

    engine = EmbeddingSimilarityEngine()

    results = engine.rank(
        query=("distributed systems " "consistency scaling"),
        records=embedding_records,
    )

    print()
    print("EMBEDDING RETRIEVAL")

    print()

    for index, (
        record,
        similarity,
    ) in enumerate(
        results[:3],
        start=1,
    ):

        print()

        print(f"RESULT #{index}")

        print()

        print(record.content)

        print()

        print(f"similarity: " f"{similarity}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
