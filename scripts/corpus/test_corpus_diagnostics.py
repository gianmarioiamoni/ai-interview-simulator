# scripts/test_corpus_diagnostics.py

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


def main():

    # -------------------------------------------------
    # INGESTION
    # -------------------------------------------------

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path=("data/sample_questions.json"),
        source="sample_dataset",
    )

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(
        raw_records,
    )

    classifier = QuestionMetadataClassifier()

    classified = classifier.classify(
        normalized,
    )

    mapper = QuestionBankItemMapper()

    items = mapper.map(
        classified,
    )

    # -------------------------------------------------
    # DIAGNOSTICS
    # -------------------------------------------------

    engine = CorpusDiagnosticsEngine()

    report = engine.analyze(
        items,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("CORPUS DIAGNOSTICS")
    print()

    print(
        report.model_dump_json(
            indent=2,
        )
    )

    print()


if __name__ == "__main__":
    main()
