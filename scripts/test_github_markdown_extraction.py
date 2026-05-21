# scripts/test_github_markdown_extraction.py

from pathlib import Path

from services.question_ingestion.contracts import (
    GitHubDocument,
)

from services.question_ingestion.github_markdown_extractor import (
    GitHubMarkdownExtractor,
)


def main() -> None:

    # -------------------------------------------------
    # LOAD REAL MARKDOWN CORPUS
    # -------------------------------------------------

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

    # -------------------------------------------------
    # EXTRACTION
    # -------------------------------------------------

    extractor = GitHubMarkdownExtractor()

    questions = extractor.extract_questions(
        document=document,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("GITHUB MARKDOWN EXTRACTION")

    print()

    print(f"TOTAL QUESTIONS: " f"{len(questions)}")

    for index, question in enumerate(
        questions,
        start=1,
    ):

        print()

        print(f"QUESTION #{index}")

        print()

        print(question)

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
