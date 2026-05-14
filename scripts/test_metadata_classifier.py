# scripts/test_metadata_classifier.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_ingestion.classifiers.question_metadata_classifier import (
    QuestionMetadataClassifier,
)


def main():

    loader = JSONDatasetLoader()

    records = loader.load(
        dataset_path="datasets/sample_questions.json",
        source="sample_dataset",
    )

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(records)

    classifier = QuestionMetadataClassifier()

    classified = classifier.classify(normalized)

    print()

    print("CLASSIFIED RECORDS:", len(classified))

    print()

    for item in classified:
        print(item)

        print()


if __name__ == "__main__":
    main()
