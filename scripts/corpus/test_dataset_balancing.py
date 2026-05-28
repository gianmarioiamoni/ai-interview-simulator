# scripts/test_dataset_balancing.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_ingestion.classifiers.question_metadata_classifier import (
    QuestionMetadataClassifier,
)

from services.question_ingestion.mappers.question_bank_item_mapper import (
    QuestionBankItemMapper,
)

from services.question_intelligence.balancing.dataset_balancing_engine import (
    DatasetBalancingEngine,
)


def main():

    # -------------------------------------------------
    # INGESTION
    # -------------------------------------------------

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path=("data/sample_questions.json"),
        source="sample_dataset",
    )

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(
        raw_records,
    )

    classifier = QuestionMetadataClassifier()

    classified = classifier.classify(
        normalized,
    )

    mapper = QuestionBankItemMapper()

    items = mapper.map(
        classified,
    )

    # -------------------------------------------------
    # BALANCING
    # -------------------------------------------------

    engine = DatasetBalancingEngine()

    report = engine.analyze(
        items,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("DATASET BALANCING REPORT")
    print()

    print(f"TOTAL ISSUES: " f"{report.total_issues}")

    print()

    for idx, issue in enumerate(
        report.issues,
        start=1,
    ):

        print(f"ISSUE #{idx}")
        print()

        print(
            issue.model_dump_json(
                indent=2,
            )
        )

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
