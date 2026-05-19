# scripts/test_external_dataset_ingestion.py

import json

from pathlib import Path

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_ingestion.dataset_registry_loader import (
    DatasetRegistryLoader,
)

from services.question_ingestion.adapters.adapter_registry import (
    AdapterRegistry,
)


def main() -> None:
    # =====================================================
    # DATASET CONFIG
    # =====================================================

    dataset_name = "system_design_dataset"

    dataset_path = (
    "datasets/external/" 
    "system_design_dataset.json"
    )
    # =====================================================
    # LOAD DATASET
    # =====================================================

    dataset_path = "datasets/external/system_design_dataset.json"

    from services.question_ingestion.adapters.system_design_dataset_adapter import (
        SystemDesignDatasetAdapter,
    )

    from services.question_ingestion.contracts import (
        RawQuestionRecord,
    )

    # =====================================================
    # LOAD DATASET REGISTRY
    # =====================================================

    registry_loader = DatasetRegistryLoader()

    descriptors = registry_loader.load(path=("datasets/" "dataset_registry.json"))

    descriptor = next(
        (item for item in descriptors if item.name == dataset_name),
        None,
    )

    if descriptor is None:

        raise ValueError(
            (
                "Dataset descriptor " 
                "not found: " 
                f"{dataset_name}"
            )
        )
    # =====================================================
    # RESOLVE ADAPTER
    # =====================================================

    adapter_registry = AdapterRegistry()

    adapter = adapter_registry.get(descriptor.adapter_name)
    
    # =====================================================
    # LOAD RAW JSON
    # =====================================================

    with open(
        dataset_path,
        "r",
        encoding="utf-8",
    ) as f:

        raw_data = json.load(f)

    # =====================================================
    # ADAPTER
    # =====================================================

    raw_records: list[RawQuestionRecord] = []

    for item in raw_data:

        raw_records.append(
            adapter.adapt(
                payload=item,
                source=descriptor.name,
                source_type=descriptor.source_type,
                dataset_version="v1",
            )
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
