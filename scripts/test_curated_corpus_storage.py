# scripts/test_curated_corpus_storage.py

from services.question_ingestion.contracts import (
    GitHubDocument,
)

from services.question_ingestion.corpus_onboarding_service import (
    CorpusOnboardingService,
)

from services.question_ingestion.curated_corpus_storage import (
    CuratedCorpusStorage,
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

Paris is the capital of France.
"""

    document = GitHubDocument(
        path="README.md",
        content=content,
        repository=("tech_interview_handbook"),
        branch="main",
    )

    onboarding_service = CorpusOnboardingService()

    onboarding_result = onboarding_service.onboard(document)

    storage = CuratedCorpusStorage()

    output_path = "datasets/curated/" "tech_interview_handbook.json"

    storage.persist(
        onboarding_result=(onboarding_result),
        output_path=output_path,
        corpus_version="v1",
    )

    print()
    print("CURATED CORPUS STORAGE")

    print()

    print(f"repository: " f"{onboarding_result.repository_name}")

    print(f"stored_questions: " f"{onboarding_result.accepted_questions}")

    print()

    print(f"output: " f"{output_path}")

    print()

    print("-" * 80)


if __name__ == "__main__":

    main()
