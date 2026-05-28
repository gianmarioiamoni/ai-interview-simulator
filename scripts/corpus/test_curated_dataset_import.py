# scripts/test_curated_dataset_import.py

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_ingestion.classifiers.question_metadata_classifier import (
    QuestionMetadataClassifier,
)

from services.question_ingestion.mappers.question_bank_item_mapper import (
    QuestionBankItemMapper,
)

from services.question_intelligence.corpus.corpus_diagnostics_engine import (
    CorpusDiagnosticsEngine,
)

from services.question_intelligence.balancing.dataset_balancing_engine import (
    DatasetBalancingEngine,
)


def main():

    # -------------------------------------------------
    # LOAD
    # -------------------------------------------------

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path=("data/curated_engineering_questions.json"),
        source="curated_engineering",
    )

    # -------------------------------------------------
    # NORMALIZE
    # -------------------------------------------------

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(
        raw_records,
    )

    # -------------------------------------------------
    # CLASSIFY
    # -------------------------------------------------

    classifier = QuestionMetadataClassifier()

    classified = classifier.classify(
        normalized,
    )

    # -------------------------------------------------
    # MAP
    # -------------------------------------------------

    mapper = QuestionBankItemMapper()

    items = mapper.map(
        classified,
    )

    # -------------------------------------------------
    # CORPUS
    # -------------------------------------------------

    corpus_engine = CorpusDiagnosticsEngine()

    corpus_report = corpus_engine.analyze(
        items,
    )

    # -------------------------------------------------
    # BALANCING
    # -------------------------------------------------

    balancing_engine = DatasetBalancingEngine()

    balancing_report = balancing_engine.analyze(
        items,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("CURATED DATASET IMPORT")
    print()

    print(
        corpus_report.model_dump_json(
            indent=2,
        )
    )

    print()

    print(
        balancing_report.model_dump_json(
            indent=2,
        )
    )

    print()


if __name__ == "__main__":
    main()
