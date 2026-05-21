# scripts/test_real_corpus_onboarding.py

from services.question_ingestion.github_markdown_extractor import (
    GitHubMarkdownExtractor,
)

from services.question_ingestion.corpus_semantic_validator import (
    CorpusSemanticValidator,
)

from services.question_ingestion.corpus_onboarding_service import (
    CorpusOnboardingService,
)

from services.question_ingestion.curated_corpus_storage import (
    CuratedCorpusStorage,
)


def main() -> None:

    # -------------------------------------------------
    # EXTRACT
    # -------------------------------------------------

    extractor = GitHubMarkdownExtractor()

    questions = extractor.extract_questions(
        markdown_path=("datasets/raw/github/" "backend_scalability.md")
    )

    # -------------------------------------------------
    # VALIDATE
    # -------------------------------------------------

    validator = CorpusSemanticValidator()

    validated = validator.validate(
        questions=questions,
        source_name=("backend_scalability"),
        source_type="github",
        dataset_version="v1",
    )

    # -------------------------------------------------
    # ONBOARD
    # -------------------------------------------------

    onboarding = CorpusOnboardingService()

    result = onboarding.onboard(
        repository_name=("backend_scalability"),
        validated_records=(validated),
    )

    # -------------------------------------------------
    # STORE
    # -------------------------------------------------

    storage = CuratedCorpusStorage()

    output_path = storage.store(
        repository_name=("backend_scalability"),
        records=(result.accepted_questions),
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("REAL CORPUS ONBOARDING")

    print()

    print(f"repository: " f"{result.repository_name}")

    print()

    print(f"total_questions: " f"{result.total_questions}")

    print(f"accepted_questions: " f"{result.accepted_questions_count}")

    print(f"rejected_questions: " f"{result.rejected_questions_count}")

    print()

    print(f"average_score: " f"{result.average_score}")

    print()

    print(f"decision: " f"{result.decision}")

    print()

    print(f"output: " f"{output_path}")

    print()

    print("SAMPLE QUESTIONS")

    print()

    for index, question in enumerate(
        result.accepted_questions[:5],
        start=1,
    ):

        print(f"QUESTION #{index}")

        print()

        print(question.content)

        print()

        print(f"categories: " f"{question.semantic_categories}")

        print()

        print(f"score: " f"{question.semantic_score}")

        print()

        print("-" * 80)

        print()


if __name__ == "__main__":

    main()
