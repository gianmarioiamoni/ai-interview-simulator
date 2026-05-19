# scripts/test_external_dataset_ingestion.py

import json

from pathlib import Path

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


def main() -> None:

    # =====================================================
    # LOAD DATASET
    # =====================================================

    dataset_path = "datasets/external/system_design_dataset.json"

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path=dataset_path,
        source="system_design_dataset",
    )

    print()
    print("RAW RECORDS")
    print()

    print(f"TOTAL: " f"{len(raw_records)}")

    # =====================================================
    # NORMALIZATION
    # =====================================================

    normalizer = QuestionNormalizer()

    normalized_records = normalizer.normalize(raw_records)

    print()
    print("NORMALIZED RECORDS")
    print()

    print(f"TOTAL: " f"{len(normalized_records)}")

    # =====================================================
    # OUTPUT
    # =====================================================

    for index, record in enumerate(
        normalized_records,
        start=1,
    ):

        print()

        print(f"RECORD #{index}")

        print()

        print(record.text)

        print()

        print(f"source: " f"{record.source}")

        print(f"source_type: " f"{record.ingestion_metadata.source_type}")

        print(f"dataset_version: " f"{record.ingestion_metadata.dataset_version}")

        print()

        print(f"role_hint: " f"{record.role_hint}")

        print(f"area_hint: " f"{record.area_hint}")

        print(f"level_hint: " f"{record.level_hint}")

        print(f"difficulty_hint: " f"{record.difficulty_hint}")

        print()

        print("INGESTION METADATA")

        print()

        print(
            json.dumps(
                (
                    record.ingestion_metadata.model_dump(
                        mode="json",
                    )
                ),
                indent=2,
            )
        )

        print()
        print("-" * 80)


if __name__ == "__main__":

    main()
