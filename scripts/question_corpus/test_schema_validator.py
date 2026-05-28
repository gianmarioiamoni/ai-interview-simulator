# scripts/question_corpus/test_schema_validator.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.validations.corpus_schema_validator import CorpusSchemaValidator


def main() -> None:

    loader = FolderCorpusLoader()

    validator = CorpusSchemaValidator()

    corpus = loader.load(
        "datasets/curated/interview_seed",
    )

    report = validator.validate(
        corpus.questions,
    )

    print("\nSCHEMA VALIDATION REPORT\n")

    print(f"Questions: {report.total_questions}")
    print(f"Issues: {report.total_issues}")
    print(f"Errors: {report.errors}")
    print(f"Warnings: {report.warnings}")

    if report.issues:

        print("\nDETAILS\n")

        for issue in report.issues:

            print(
                f"[{issue.severity.upper()}] " f"{issue.category}: " f"{issue.message}"
            )


if __name__ == "__main__":

    main()
