# scripts/test_dataset_discovery_registry.py

from services.question_ingestion.dataset_discovery_registry_loader import (
    DatasetDiscoveryRegistryLoader,
)


def main() -> None:

    loader = DatasetDiscoveryRegistryLoader()

    candidates = loader.load(path=("datasets/" "dataset_discovery_registry.json"))

    print()
    print("DATASET DISCOVERY REGISTRY")

    print()

    print(f"TOTAL DATASETS: " f"{len(candidates)}")

    for index, dataset in enumerate(
        candidates,
        start=1,
    ):

        print()

        print(f"DATASET #{index}")

        print()

        print(f"name: " f"{dataset.name}")

        print(f"source: " f"{dataset.source}")

        print(f"domain: " f"{dataset.domain}")

        print(f"quality: " f"{dataset.estimated_quality}")

        print(f"noise: " f"{dataset.estimated_noise}")

        print(f"status: " f"{dataset.ingestion_status}")

        print(f"adapter: " f"{dataset.adapter_name}")

        print()

        print(f"notes: " f"{dataset.notes}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
