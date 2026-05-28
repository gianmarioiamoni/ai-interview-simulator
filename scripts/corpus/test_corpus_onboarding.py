# scripts/test_corpus_onboarding.py

from services.question_ingestion.contracts import (
    GitHubDocument,
)

from services.question_ingestion.corpus_onboarding_service import (
    CorpusOnboardingService,
)


def main() -> None:

    content = """
# Technical Questions

- How would you design a distributed cache?
- Explain eventual consistency trade-offs.
- What is database sharding?
- Describe Kubernetes deployment strategies.
- Explain mutexes and deadlocks.

# Noise

The weather is sunny today.

Paris is the capital of France.
"""

    document = GitHubDocument(
        path="README.md",
        content=content,
        repository=("tech_interview_handbook"),
        branch="main",
    )

    service = CorpusOnboardingService()

    result = service.onboard(document)

    print()
    print("CORPUS ONBOARDING")

    print()

    print(f"repository: " f"{result.repository_name}")

    print()

    print(f"total_questions: " f"{result.total_questions}")

    print(f"accepted_questions: " f"{result.accepted_questions}")

    print(f"rejected_questions: " f"{result.rejected_questions}")

    print(f"average_score: " f"{result.average_score}")

    print()

    print(f"decision: " f"{result.onboarding_decision}")

    print()

    print("ACCEPTED QUESTIONS")

    for index, item in enumerate(
        result.accepted_results,
        start=1,
    ):

        print()

        print(f"QUESTION #{index}")

        print()

        print(item.raw_question)

        print()

        print(f"score: " f"{item.filter_result.score}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
