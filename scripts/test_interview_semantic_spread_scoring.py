# scripts/test_interview_semantic_spread_scoring.py

from services.interview_orchestration.interview_semantic_spread_scorer import (
    InterviewSemanticSpreadScorer,
)


def main() -> None:

    scorer = InterviewSemanticSpreadScorer()

    test_values = [
        0.18,
        0.34,
        0.58,
        0.81,
    ]

    print()

    print("INTERVIEW SEMANTIC SPREAD SCORING")

    for similarity in test_values:

        result = scorer.score(average_similarity=(similarity))

        print()

        print(f"similarity: " f"{result.average_similarity}")

        print(f"spread_score: " f"{result.spread_score}")

        print(f"classification: " f"{result.classification}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
