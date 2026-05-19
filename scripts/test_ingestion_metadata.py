# scripts/test_ingestion_metadata.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)
from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


def main():

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path="data/sample_questions.json",
        source="sample_dataset",
    )

    print()
    print(f"RAW RECORDS: {len(raw_records)}")
    print()

    normalizer = QuestionNormalizer()

    records = normalizer.normalize(
        raw_records,
    )

    print()
    print(f"NORMALIZED RECORDS: {len(records)}")
    print()

    print()
    print("INGESTION METADATA")
    print()

    for idx, record in enumerate(
        records[:3],
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
