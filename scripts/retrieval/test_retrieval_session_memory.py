# scripts/test_retrieval_session_memory.py

from services.retrieval.retrieval_session_memory import (
    RetrievalSessionMemory,
)


def main() -> None:

    memory = RetrievalSessionMemory(
        max_history=5,
    )

    questions = [
        ("How would you design " "a distributed cache?"),
        ("Explain eventual " "consistency."),
        ("What is " "database sharding?"),
    ]

    # -------------------------------------------------
    # STORE
    # -------------------------------------------------

    for question in questions:

        memory.remember(question)

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("RETRIEVAL SESSION MEMORY")

    print()

    print("RECENT QUESTIONS")

    print()

    for index, question in enumerate(
        memory.get_recent_questions(),
        start=1,
    ):

        print(f"{index}. " f"{question}")

    print()

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------

    lookup = "How would you design " "a distributed cache?"

    print(f"has_seen: " f"{memory.has_seen(lookup)}")

    print()


if __name__ == "__main__":

    main()
