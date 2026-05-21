# scripts/test_real_corpus_onboarding.py

from pathlib import Path

from services.question_ingestion.contracts import GitHubDocument
from services.question_ingestion.github_markdown_extractor import GitHubMarkdownExtractor
from services.question_ingestion.corpus_onboarding_service import CorpusOnboardingService
from services.question_ingestion.curated_corpus_storage import CuratedCorpusStorage


def main() -> None:

    # =================================================
    # LOAD REAL CORPUS
    # =================================================

    markdown_path = "datasets/raw/github/" "backend_scalability.md"

    content = Path(markdown_path).read_text(
        encoding="utf-8",
    )

    document = GitHubDocument(
        path=markdown_path,
        content=content,
        repository=("backend_scalability"),
        branch="main",
    )

    # =================================================
    # EXTRACTION
    # =================================================

    extractor = GitHubMarkdownExtractor()

    questions = extractor.extract_questions(
        document=document,
    )

    # =================================================
    # ONBOARDING
    # =================================================

    onboarding = CorpusOnboardingService()

    onboarding_result = onboarding.onboard(document=document)

    # =================================================
    # STORAGE
    # =================================================

    storage = CuratedCorpusStorage()

    output_path = (
        "datasets/curated/github/"
        "backend_scalability.json"
    )

    storage.persist(
        onboarding_result=(onboarding_result),
        output_path=(output_path),
        corpus_version="v1",
    )

    # =================================================
    # OUTPUT
    # =================================================

    print()

    print("REAL CORPUS ONBOARDING")

    print()

    print(f"repository: " f"{onboarding_result.repository_name}")

    print()

    print(f"total_questions: " f"{onboarding_result.total_questions}")

    print(f"accepted_questions: " f"{onboarding_result.accepted_questions}")

    print(f"rejected_questions: " f"{onboarding_result.rejected_questions}")

    print()

    print(f"average_score: " f"{onboarding_result.average_score}")

    print()

    print(f"decision: " f"{onboarding_result.onboarding_decision}")

    print()

    print(f"output: " f"{output_path}")

    print()

    print("SAMPLE QUESTIONS")

    print()

    for index, question in enumerate(
        onboarding_result.accepted_results[:10],
        start=1,
    ):

        print(f"QUESTION #{index}")

        print()

        print(question.raw_question)

        print()

        print(f"categories: " f"{question.filter_result.matched_categories}")

        print()

        print(f"score: " f"{question.filter_result.score}")

        print()

        print("-" * 80)

        print()


if __name__ == "__main__":

    main()
