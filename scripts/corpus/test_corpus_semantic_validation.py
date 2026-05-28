# scripts/test_corpus_semantic_validation.py

from services.question_ingestion.contracts import (
    GitHubDocument,
)

from services.question_ingestion.github_markdown_extractor import (
    GitHubMarkdownExtractor,
)

from services.question_ingestion.corpus_semantic_validator import (
    CorpusSemanticValidator,
)


def main() -> None:

    content = """
# Engineering Questions

- How would you design a distributed cache?
- Explain eventual consistency trade-offs.
- What is database sharding?
- Describe Kubernetes deployment strategies.
- Explain mutexes and deadlocks.

# Noise

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

    validator = CorpusSemanticValidator()

    questions = extractor.extract_questions(document)

    results = validator.validate(
        questions=questions,
        source_name=("tech_interview_handbook"),
        source_type="github",
        dataset_version="v1",
    )

    print()
    print("CORPUS SEMANTIC VALIDATION")

    print()

    print(f"TOTAL QUESTIONS: " f"{len(results)}")

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(f"QUESTION #{index}")

        print()

        print(result.raw_question)

        print()

        print(f"technical: " f"{result.filter_result.is_technical}")

        print(f"score: " f"{result.filter_result.score}")

        print(f"categories: " f"{result.filter_result.matched_categories}")

        print(f"matched_terms: " f"{result.filter_result.matched_terms}")

        print()

        print("NORMALIZED" if result.normalized_record else "REJECTED")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
