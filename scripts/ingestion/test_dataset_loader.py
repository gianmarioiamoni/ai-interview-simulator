# scripts/test_dataset_loader.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)


def main():

    loader = JSONDatasetLoader()

    records = loader.load(
        dataset_path="datasets/sample_questions.json",
        source="sample_dataset",
    )

    print()

    print("TOTAL RECORDS:", len(records))

    print()

    for r in records:
        print(r)

        print()


if __name__ == "__main__":
    main()
