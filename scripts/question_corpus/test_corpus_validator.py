# scripts/question_corpus/test_corpus_validator.py

from services.question_corpus.loaders.folder_corpus_loader import (
    FolderCorpusLoader,
)

from services.question_corpus.validators.corpus_validator import (
    CorpusValidator,
)


def main() -> None:

    loader = FolderCorpusLoader()

    validator = CorpusValidator()

    corpus = loader.load("datasets/curated/interview_seed")

    report = validator.validate(
        corpus,
    )

    print("\nCORPUS VALIDATION REPORT\n")

    print(f"Questions: {report.total_questions}")
    print(f"Issues: {report.total_issues}")

    for issue in report.issues:

        print("\n-------------------------")
        print(f"Question: {issue.question_id}")
        print(f"Type: {issue.issue_type}")
        print(f"Severity: {issue.severity}")
        print(f"Description: {issue.description}")


if __name__ == "__main__":

    main()
