# scripts/test_deduplicated_corpus_builder.py

from services.question_intelligence.deduplicated_corpus_builder import (
    DeduplicatedCorpusBuilder,
)


def main() -> None:

    questions = [
        # -------------------------------------------------
        # DUPLICATES
        # -------------------------------------------------
        ("How would you design " "a distributed cache?"),
        ("How would you architect " "a distributed caching system?"),
        # -------------------------------------------------
        # UNIQUE
        # -------------------------------------------------
        ("Explain quorum-based " "replication."),
        ("How would you " "design a CDN?"),
        ("Explain eventual " "consistency trade-offs."),
    ]

    builder = DeduplicatedCorpusBuilder()

    cleaned = builder.build(
        questions=questions,
    )

    print()

    print("DEDUPLICATED CORPUS")

    print()

    print(f"ORIGINAL QUESTIONS: " f"{len(questions)}")

    print(f"CLEANED QUESTIONS: " f"{len(cleaned)}")

    print()

    for index, question in enumerate(
        cleaned,
        start=1,
    ):

        print(f"QUESTION #{index}")

        print()

        print(question)

        print()

        print("-" * 80)

        print()


if __name__ == "__main__":

    main()
