# scripts/test_multiformat_ingestion.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.loaders.jsonl_dataset_loader import (
    JSONLDatasetLoader,
)

from services.question_ingestion.loaders.csv_dataset_loader import (
    CSVDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


def main():

    normalizer = QuestionNormalizer()

    # -------------------------------------------------
    # JSON
    # -------------------------------------------------

    json_loader = JSONDatasetLoader()

    json_records = json_loader.load(
        dataset_path=("data/sample_questions.json"),
        source="json_dataset",
    )

    normalized_json = normalizer.normalize(
        json_records,
    )

    # -------------------------------------------------
    # JSONL
    # -------------------------------------------------

    jsonl_loader = JSONLDatasetLoader()

    jsonl_records = jsonl_loader.load(
        dataset_path=("data/sample_questions.jsonl"),
        source="jsonl_dataset",
    )

    normalized_jsonl = normalizer.normalize(
        jsonl_records,
    )

    # -------------------------------------------------
    # CSV
    # -------------------------------------------------

    csv_loader = CSVDatasetLoader()

    csv_records = csv_loader.load(
        dataset_path=("data/sample_questions.csv"),
        source="csv_dataset",
    )

    normalized_csv = normalizer.normalize(
        csv_records,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("MULTI-FORMAT INGESTION")
    print()

    print(f"JSON: " f"{len(normalized_json)}")

    print(f"JSONL: " f"{len(normalized_jsonl)}")

    print(f"CSV: " f"{len(normalized_csv)}")

    print()

    all_records = normalized_json + normalized_jsonl + normalized_csv

    for idx, record in enumerate(
        all_records,
        start=1,
    ):

        print(f"RECORD #{idx}")
        print()

        print(record.text)
        print()

        print(
            record.ingestion_metadata.model_dump_json(
                indent=2,
            )
        )

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
