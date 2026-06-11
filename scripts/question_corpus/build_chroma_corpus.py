# scripts/question_corpus/build_chroma_corpus.py

from collections import Counter

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from services.question_corpus.adapters.langchain_corpus_adapter import LangChainCorpusAdapter
from services.question_corpus.builders.retrieval_corpus_builder import RetrievalCorpusBuilder
from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)
from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.dedup.corpus_id_deduplicator import CorpusIdDeduplicator
from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService
from services.question_corpus.vectorstores.chroma_corpus_builder import ChromaCorpusBuilder

SOURCE_ROOTS = [
    "datasets/curated/hf_import",
    "datasets/curated/interview_seed",
    "datasets/curated/local_import",
]

EXPECTED_RAW_COUNT = 836
EXPECTED_INDEXED_COUNT = 831

REQUIRED_METADATA_KEYS = (
    "area",
    "role",
    "seniority",
    "difficulty",
    "source",
    "document_id",
)

VALIDATION_AREAS = (
    "technical_case_study",
    "technical_database",
    "technical_coding",
    "hr_situational",
)

AREA_SAMPLE_QUERIES = {
    "technical_case_study": "design a scalable notification system",
    "technical_database": "sql query optimization indexing transactions",
    "technical_coding": "binary search tree algorithm implementation",
    "hr_situational": "describe a conflict with a teammate and how you resolved it",
}


def load_merged_corpus() -> CuratedCorpus:

    loader = FolderCorpusLoader()

    questions = []

    for source_root in SOURCE_ROOTS:

        corpus = loader.load(
            source_root,
        )

        questions.extend(
            corpus.questions,
        )

    return CuratedCorpus(
        questions=questions,
    )


def validate_metadata(
    chroma: Chroma,
) -> dict[str, int | list[str]]:

    sample = chroma._collection.get(
        limit=50,
        include=["metadatas"],
    )

    metadatas = sample.get(
        "metadatas",
        [],
    )

    missing_counts: Counter[str] = Counter()

    for metadata in metadatas:

        for key in REQUIRED_METADATA_KEYS:

            value = metadata.get(
                key,
            )

            if value is None or value == "":

                missing_counts[key] += 1

    missing_summary = dict(missing_counts)

    return {
        "samples_checked": len(metadatas),
        "missing_fields": missing_summary,
    }


def validate_area_filters(
    retrieval_service: ChromaRetrievalService,
) -> dict[str, int]:

    area_counts: dict[str, int] = {}

    for area in VALIDATION_AREAS:

        query = AREA_SAMPLE_QUERIES[area]

        filters = RetrievalFilters(
            area=area,
        )

        results = retrieval_service.search_with_filters(
            query=query,
            filters=filters,
            k=5,
        )

        area_counts[area] = len(results)

    return area_counts


def print_sample_retrieval(
    retrieval_service: ChromaRetrievalService,
    area: str,
) -> None:

    query = AREA_SAMPLE_QUERIES[area]

    filters = RetrievalFilters(
        area=area,
    )

    results = retrieval_service.search_with_filters(
        query=query,
        filters=filters,
        k=2,
    )

    print(f"\nSAMPLE RETRIEVAL — {area}")
    print("-" * 60)
    print(f"query: {query}")
    print(f"results: {len(results)}")

    for index, result in enumerate(results):

        metadata = result.document.metadata

        print(f"\n  #{index + 1} score={result.final_score}")
        print(f"     document_id: {metadata.get('document_id')}")
        print(f"     area:        {metadata.get('area')}")
        print(f"     role:        {metadata.get('role')}")
        print(f"     seniority:   {metadata.get('seniority')}")
        print(f"     difficulty:  {metadata.get('difficulty')}")
        print(f"     source:      {metadata.get('source')}")
        print(f"     text:        {result.document.page_content[:120]}...")


def main() -> None:

    load_dotenv()

    print("\nCHROMA CORPUS BUILD")
    print("=" * 60)

    corpus = load_merged_corpus()

    raw_count = len(corpus.questions)

    print(f"\nraw_count: {raw_count}")

    deduplicator = CorpusIdDeduplicator()

    deduplicated_questions, skipped_count = deduplicator.deduplicate(
        corpus.questions,
    )

    indexed_count = len(deduplicated_questions)

    print(f"skipped_duplicates: {skipped_count}")
    print(f"indexed_count: {indexed_count}")

    if raw_count != EXPECTED_RAW_COUNT:

        print(
            f"\nWARNING: raw_count {raw_count} != expected {EXPECTED_RAW_COUNT}",
        )

    if indexed_count != EXPECTED_INDEXED_COUNT:

        print(
            f"\nWARNING: indexed_count {indexed_count} != expected {EXPECTED_INDEXED_COUNT}",
        )

    deduplicated_corpus = CuratedCorpus(
        questions=deduplicated_questions,
    )

    retrieval_builder = RetrievalCorpusBuilder(
        skip_embedding=True,
    )

    retrieval_documents = retrieval_builder.build(
        deduplicated_corpus,
    )

    langchain_documents = LangChainCorpusAdapter().adapt(
        retrieval_documents,
    )

    ChromaCorpusBuilder().build(
        langchain_documents,
    )

    chroma = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=OpenAIEmbeddings(),
        persist_directory=CHROMA_PERSIST_DIRECTORY,
    )

    final_count = chroma._collection.count()

    print(f"\nchroma_document_count: {final_count}")

    metadata_validation = validate_metadata(
        chroma,
    )

    print("\nMETADATA VALIDATION")
    print("-" * 60)
    print(f"samples_checked: {metadata_validation['samples_checked']}")
    print(f"missing_fields:  {metadata_validation['missing_fields']}")

    retrieval_service = ChromaRetrievalService()

    area_filter_counts = validate_area_filters(
        retrieval_service,
    )

    print("\nAREA-FILTERED RETRIEVAL")
    print("-" * 60)

    for area, count in area_filter_counts.items():

        print(f"  {area}: {count} results")

    for area in VALIDATION_AREAS:

        print_sample_retrieval(
            retrieval_service,
            area,
        )

    print("\nCHROMA BUILD COMPLETED\n")


if __name__ == "__main__":

    main()
