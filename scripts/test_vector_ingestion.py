# scripts/test_vector_ingestion.py

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

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

from services.question_ingestion.indexers.question_vector_indexer import (
    QuestionVectorIndexer,
)


def main():

    # -------------------------------------------------
    # LOAD
    # -------------------------------------------------

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path="datasets/seed_questions.json",
        source="seed_dataset",
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
    # VECTOR STORE
    # -------------------------------------------------

    chroma_store = ChromaQuestionStore()

    vector_store = QuestionVectorStore(
        chroma_store,
    )

    # -------------------------------------------------
    # INDEXER
    # -------------------------------------------------

    indexer = QuestionVectorIndexer(
        vector_store,
    )

    indexed = indexer.index(
        items,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("INDEXED DOCUMENTS:", indexed)

    print()


if __name__ == "__main__":
    main()
