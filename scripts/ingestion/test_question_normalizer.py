# scripts/test_question_normalizer.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


def main():

    loader = JSONDatasetLoader()

    records = loader.load(
        dataset_path="datasets/sample_questions.json",
        source="sample_dataset",
    )

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(records)

    print()

    print("NORMALIZED RECORDS:", len(normalized))

    print()

    for item in normalized:
        print(item)

        print()


if __name__ == "__main__":
    main()
