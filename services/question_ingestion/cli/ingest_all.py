# services/question_ingestion/cli/ingest_all.py

import json
from pathlib import Path
from time import perf_counter

from services.question_ingestion.dataset_registry_loader import DatasetRegistryLoader
from services.question_ingestion.adapters.adapter_registry import AdapterRegistry
from services.question_ingestion.loaders.json_dataset_loader import JsonDatasetLoader
from services.question_ingestion.loaders.jsonl_dataset_loader import JsonlDatasetLoader
from services.question_ingestion.loaders.csv_dataset_loader import CsvDatasetLoader
from services.question_ingestion.loaders.huggingface_dataset_loader import HuggingFaceDatasetLoader
from services.question_ingestion.normalizers.question_normalizer import QuestionNormalizer
from services.question_ingestion.mappers.question_bank_item_mapper import QuestionBankItemMapper
from services.question_ingestion.indexers.question_vector_indexer import QuestionVectorIndexer
from services.question_intelligence.deduplicated_corpus_builder import DeduplicatedCorpusBuilder
from services.question_intelligence.quality.question_set_quality_analyzer import QuestionSetQualityAnalyzer
from services.question_ingestion.diagnostics.ingestion_diagnostics_builder import IngestionDiagnosticsBuilder
from services.question_ingestion.diagnostics.ingestion_diagnostics_persistence_service import IngestionDiagnosticsPersistenceService


# =====================================================
# CONFIG
# =====================================================

DATASET_ROOT = Path("datasets")


# =====================================================
# HELPERS
# =====================================================


def _resolve_dataset_path(
    descriptor,
) -> Path:

    return DATASET_ROOT / f"{descriptor.name}.{descriptor.source_type}"


def _load_raw_records(
    descriptor,
):

    source_type = descriptor.source_type

    dataset_path = _resolve_dataset_path(
        descriptor,
    )

    # -------------------------------------------------
    # JSON
    # -------------------------------------------------

    if source_type == "json":

        loader = JsonDatasetLoader()

        return loader.load(
            dataset_path,
        )

    # -------------------------------------------------
    # JSONL
    # -------------------------------------------------

    if source_type == "jsonl":

        loader = JsonlDatasetLoader()

        return loader.load(
            dataset_path,
        )

    # -------------------------------------------------
    # CSV
    # -------------------------------------------------

    if source_type == "csv":

        loader = CsvDatasetLoader()

        return loader.load(
            dataset_path,
        )

    # -------------------------------------------------
    # HUGGINGFACE
    # -------------------------------------------------

    if source_type == "huggingface":

        loader = HuggingFaceDatasetLoader()

        return loader.load(
            descriptor.name,
        )

    raise ValueError(f"Unsupported source type: {source_type}")


# =====================================================
# MAIN
# =====================================================


def main() -> None:

    print("\nQUESTION MASS INGESTION\n")

    registry_loader = DatasetRegistryLoader()

    descriptors = registry_loader.load()

    normalizer = QuestionNormalizer()

    mapper = QuestionBankItemMapper()

    deduplicator = DeduplicatedCorpusBuilder()

    quality_analyzer = QuestionSetQualityAnalyzer()

    indexer = QuestionVectorIndexer()

    diagnostics_builder = IngestionDiagnosticsBuilder()

    diagnostics_persistence = IngestionDiagnosticsPersistenceService()

    total_ingested = 0

    # =================================================
    # PROCESS DATASETS
    # =================================================

    for descriptor in descriptors:

        start_time = perf_counter()

        try:

            print(f"\n[DATASET] {descriptor.name}")

            print(f"source_type={descriptor.source_type}")

            # -------------------------------------------------
            # LOAD RAW RECORDS
            # -------------------------------------------------

            raw_records = _load_raw_records(
                descriptor,
            )

            print(f"loaded_records={len(raw_records)}")

            # -------------------------------------------------
            # ADAPTER
            # -------------------------------------------------

            adapter = AdapterRegistry.get(
                descriptor.adapter_name,
            )

            adapted_records = adapter.adapt(
                raw_records,
            )

            print(f"adapted_records={len(adapted_records)}")

            # -------------------------------------------------
            # NORMALIZATION
            # -------------------------------------------------

            normalization_results = []

            for record in adapted_records:

                result = normalizer.normalize(
                    record,
                )

                normalization_results.append(result)

            normalized_records = [
                result.record
                for result in normalization_results
                if result.record is not None
            ]

            print(f"normalized_records={len(normalized_records)}")

            # -------------------------------------------------
            # DOMAIN MAPPING
            # -------------------------------------------------

            items = mapper.map(
                normalized_records,
            )

            print(f"mapped_items={len(items)}")

            # -------------------------------------------------
            # DEDUPLICATION
            # -------------------------------------------------

            deduplicated_items = deduplicator.build(
                items,
            )

            print(f"deduplicated_items={len(deduplicated_items)}")

            duplicate_records = len(items) - len(deduplicated_items)

            # -------------------------------------------------
            # QUALITY ANALYSIS
            # -------------------------------------------------

            quality_result = quality_analyzer.analyze(
                deduplicated_items,
            )

            print(f"quality_score={quality_result.average_quality_score}")

            print(f"average_similarity={quality_result.average_similarity}")

            # -------------------------------------------------
            # VECTOR INDEXING
            # -------------------------------------------------

            indexer.index(
                deduplicated_items,
            )

            print(f"indexed_items={len(deduplicated_items)}")

            total_ingested += len(deduplicated_items)

            # -------------------------------------------------
            # DIAGNOSTICS
            # -------------------------------------------------

            duration = round(
                perf_counter() - start_time,
                2,
            )

            diagnostics = diagnostics_builder.build(
                dataset_name=descriptor.name,
                source_type=descriptor.source_type,
                adapter_name=descriptor.adapter_name,
                raw_records=raw_records,
                normalized_records=normalized_records,
                classified_records=normalized_records,
                mapped_items=deduplicated_items,
                indexed_records=len(deduplicated_items),
                duplicate_records=duplicate_records,
                average_quality_score=(quality_result.average_quality_score),
                average_similarity=(quality_result.average_similarity),
                ingestion_duration_seconds=duration,
                success=True,
            )

            report_path = diagnostics_persistence.persist(
                diagnostics,
            )

            print(f"diagnostics_saved={report_path}")

        except Exception as exc:

            duration = round(
                perf_counter() - start_time,
                2,
            )

            diagnostics = diagnostics_builder.build(
                dataset_name=descriptor.name,
                source_type=descriptor.source_type,
                adapter_name=descriptor.adapter_name,
                raw_records=[],
                normalized_records=[],
                classified_records=[],
                mapped_items=[],
                indexed_records=0,
                duplicate_records=0,
                average_quality_score=0.0,
                average_similarity=0.0,
                ingestion_duration_seconds=duration,
                errors=[str(exc)],
                success=False,
            )

            report_path = diagnostics_persistence.persist(
                diagnostics,
            )

            print(f"[ERROR] {descriptor.name}")

            print(str(exc))

            print(f"diagnostics_saved={report_path}")

    # =================================================
    # FINAL SUMMARY
    # =================================================

    print("\nINGESTION COMPLETED\n")

    print(
        json.dumps(
            {
                "datasets_processed": len(descriptors),
                "total_ingested_items": total_ingested,
            },
            indent=2,
        )
    )


# =====================================================
# ENTRYPOINT
# =====================================================

if __name__ == "__main__":

    main()
