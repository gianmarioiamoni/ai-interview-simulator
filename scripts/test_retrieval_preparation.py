# scripts/test_retrieval_preparation.py

from services.retrieval.corpus_retrieval_preparator import (
    CorpusRetrievalPreparator,
)


def main() -> None:

    preparator = CorpusRetrievalPreparator()

    records = preparator.prepare(
        corpus_path=("datasets/curated/" "tech_interview_handbook.json")
    )

    print()
    print("RETRIEVAL PREPARATION")

    print()

    print(f"TOTAL RECORDS: " f"{len(records)}")

    for index, record in enumerate(
        records,
        start=1,
    ):

        print()

        print(f"RECORD #{index}")

        print()

        print(record.content)

        print()

        print(f"retrieval_score: " f"{record.retrieval_score}")

        print()

        print(f"categories: " f"{record.semantic_categories}")

        print()

        print(f"tags: " f"{record.retrieval_tags}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
