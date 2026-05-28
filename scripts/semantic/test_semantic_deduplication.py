# scripts/test_semantic_deduplication.py

from services.question_intelligence.semantic_duplicate_detector import (
    SemanticDuplicateDetector,
)


def main() -> None:

    questions = [
        # ---------------------------------------------
        # DUPLICATES
        # ---------------------------------------------
        ("How would you design " "a distributed cache?"),
        ("How would you architect " "a distributed caching system?"),
        ("Explain distributed " "cache design."),
        # ---------------------------------------------
        # DIFFERENT
        # ---------------------------------------------
        ("Explain quorum-based " "replication."),
        ("How would you " "design a CDN?"),
        ("Explain eventual " "consistency trade-offs."),
    ]

    detector = SemanticDuplicateDetector()

    duplicates = detector.find_duplicates(
        questions=questions,
    )

    print()

    print("SEMANTIC DEDUPLICATION")

    print()

    print(f"TOTAL DUPLICATES: " f"{len(duplicates)}")

    for index, duplicate in enumerate(
        duplicates,
        start=1,
    ):

        q1, q2, similarity = duplicate

        print()

        print(f"DUPLICATE #{index}")

        print()

        print("QUESTION 1:")

        print(q1)

        print()

        print("QUESTION 2:")

        print(q2)

        print()

        print(f"similarity: " f"{similarity}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
