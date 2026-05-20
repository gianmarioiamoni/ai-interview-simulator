# scripts/test_github_markdown_extraction.py

from services.question_ingestion.contracts import (
    GitHubDocument,
)

from services.question_ingestion.github_markdown_extractor import (
    GitHubMarkdownExtractor,
)


def main() -> None:

    content = """
# System Design Questions

- How would you design a distributed cache?
- Explain eventual consistency trade-offs.
- What is database sharding?
- Describe Kubernetes deployment strategies.

# Non Technical

Paris is the capital of France.

The weather is sunny today.
"""

    document = GitHubDocument(
        path="README.md",
        content=content,
        repository=("tech_interview_handbook"),
        branch="main",
    )

    extractor = GitHubMarkdownExtractor()

    questions = extractor.extract_questions(document)

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
