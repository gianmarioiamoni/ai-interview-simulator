# scripts/test_technical_filter.py

from services.question_quality.technical_question_filter import (
    TechnicalQuestionFilter,
)


def main() -> None:

    filter_service = TechnicalQuestionFilter()

    samples = [
        # =================================================
        # TECHNICAL
        # =================================================
        (
            "How would you design a distributed cache?",
            True,
        ),
        (
            "Explain SQL indexing strategies.",
            True,
        ),
        (
            "How does Kubernetes rolling deployment work?",
            True,
        ),
        (
            "Explain mutexes and deadlocks.",
            True,
        ),
        (
            "How does Kafka ensure message durability?",
            True,
        ),
        (
            "Explain CAP theorem trade-offs.",
            True,
        ),
        (
            "How does React virtual DOM work?",
            True,
        ),
        (
            "Explain eventual consistency in distributed systems.",
            True,
        ),
        (
            "How would you optimize API latency?",
            True,
        ),
        (
            "Explain CI/CD pipeline observability.",
            True,
        ),
        # =================================================
        # NON TECHNICAL
        # =================================================
        (
            "Who built the Notre Dame cathedral?",
            False,
        ),
        (
            "What is the capital of France?",
            False,
        ),
        (
            "Who was the president in 1995?",
            False,
        ),
        (
            "What is the population of Italy?",
            False,
        ),
        (
            "Who wrote Romeo and Juliet?",
            False,
        ),
    ]

    print()
    print("TECHNICAL FILTER")
    print()

    for (
        text,
        expected,
    ) in samples:

        result = filter_service.is_technical(text)

        categories = filter_service.matching_categories(text)

        print(text)

        print()

        print(f"expected: " f"{expected}")

        print(f"actual: " f"{result}")

        print(f"categories: " f"{categories}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
