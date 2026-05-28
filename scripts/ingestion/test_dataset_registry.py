# scripts/test_dataset_registry.py

import json

from pathlib import Path

from services.question_ingestion.contracts.dataset_descriptor import (
    DatasetDescriptor,
)


def main() -> None:

    # -------------------------------------------------
    # LOAD REGISTRY
    # -------------------------------------------------

    registry_path = Path("datasets/dataset_registry.json")

    if not registry_path.exists():

        raise FileNotFoundError(("Dataset registry not found: " f"{registry_path}"))

    with open(
        registry_path,
        "r",
        encoding="utf-8",
    ) as f:

        raw_data = json.load(f)

    # -------------------------------------------------
    # PARSE DESCRIPTORS
    # -------------------------------------------------

    descriptors = [DatasetDescriptor(**item) for item in raw_data]

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("DATASET REGISTRY")
    print()

    print(f"TOTAL DATASETS: " f"{len(descriptors)}")

    for index, descriptor in enumerate(
        descriptors,
        start=1,
    ):

        print()
        print(f"DATASET #{index}")

        print()

        print(f"name: " f"{descriptor.name}")

        print(f"domain: " f"{descriptor.domain}")

        print(f"source_type: " f"{descriptor.source_type}")

        print(f"quality_score: " f"{descriptor.quality_score}")

        print(f"trusted: " f"{descriptor.trusted}")

        print()

        print("EXPECTED SCHEMA")

        print()

        print(
            json.dumps(
                descriptor.expected_schema,
                indent=2,
            )
        )

        print()
        print("-" * 80)


if __name__ == "__main__":

    main()
