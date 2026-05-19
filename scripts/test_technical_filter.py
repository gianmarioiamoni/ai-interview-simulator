# scripts/test_technical_filter.py

from services.question_quality.technical_question_filter import (
    TechnicalQuestionFilter,
)


def main() -> None:

    filter_service = TechnicalQuestionFilter()

    samples = [
        # technical
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
        # non technical
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
    ]

    print()
    print("TECHNICAL FILTER")
    print()

    for text, expected in samples:

        result = filter_service.is_technical(text)

        print(text)

        print()

        print(f"expected: {expected}")

        print(f"actual: {result}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
