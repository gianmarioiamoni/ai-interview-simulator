# scripts/test_adapter_registry.py

from services.question_ingestion.dataset_registry_loader import (
    DatasetRegistryLoader,
)

from services.question_ingestion.adapters.adapter_registry import (
    AdapterRegistry,
)


def main() -> None:

    # =====================================================
    # LOAD DATASET REGISTRY
    # =====================================================

    registry_loader = DatasetRegistryLoader()

    descriptors = registry_loader.load(path=("datasets/" "dataset_registry.json"))

    # =====================================================
    # ADAPTER REGISTRY
    # =====================================================

    adapter_registry = AdapterRegistry()

    # =====================================================
    # OUTPUT
    # =====================================================

    print()
    print("ADAPTER REGISTRY")
    print()

    print(f"TOTAL DATASETS: " f"{len(descriptors)}")

    for index, descriptor in enumerate(
        descriptors,
        start=1,
    ):

        adapter = adapter_registry.get(descriptor.adapter_name)

        print()

        print(f"DATASET #{index}")

        print()

        print(f"name: " f"{descriptor.name}")

        print(f"domain: " f"{descriptor.domain}")

        print(f"source_type: " f"{descriptor.source_type}")

        print(f"adapter_name: " f"{descriptor.adapter_name}")

        print(f"adapter_class: " f"{adapter.__class__.__name__}")

        print(f"quality_score: " f"{descriptor.quality_score}")

        print(f"trusted: " f"{descriptor.trusted}")

        print()
        print("-" * 80)


if __name__ == "__main__":

    main()
