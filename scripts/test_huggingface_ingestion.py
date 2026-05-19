# scripts/test_huggingface_ingestion.py

from services.question_ingestion.loaders.huggingface_dataset_loader import (
    HuggingFaceDatasetLoader,
)

from services.question_ingestion.adapters.adapter_registry import (
    AdapterRegistry,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


def main() -> None:

    # =====================================================
    # ADAPTER
    # =====================================================

    registry = AdapterRegistry()

    adapter = registry.get("huggingface_qa")

    # =====================================================
    # LOADER
    # =====================================================

    loader = HuggingFaceDatasetLoader()

    raw_records = loader.load(
        dataset_name="squad",
        split="train[:20]",
        source="squad_dataset",
        source_type="huggingface",
        dataset_version="v1",
        adapter=adapter,
        limit=20,
    )

    print()
    print("RAW RECORDS")
    print()

    print(f"TOTAL: " f"{len(raw_records)}")

    # =====================================================
    # NORMALIZATION
    # =====================================================

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(raw_records)

    print()
    print("NORMALIZED RECORDS")
    print()

    print(f"TOTAL: " f"{len(normalized)}")

    for index, item in enumerate(
        normalized[:5],
        start=1,
    ):

        print()

        print(f"QUESTION #{index}")

        print()

        print(item.text)

        print()

        print(f"role: " f"{item.role_hint}")

        print(f"area: " f"{item.area_hint}")

        print(f"level: " f"{item.level_hint}")

        print(f"difficulty: " f"{item.difficulty_hint}")

        print()
        print("-" * 80)


if __name__ == "__main__":

    main()
