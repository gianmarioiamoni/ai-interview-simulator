# scripts/question_corpus/import_database_hf_dataset.py

import json
from pathlib import Path

from datasets import load_dataset

from domain.contracts.corpus.curated_question import CuratedQuestion
from services.question_ingestion.adapters.huggingface_database_adapter import (
    HuggingFaceDatabaseAdapter,
)
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)
from services.question_ingestion.reporting.corpus_import_reporter import (
    CorpusImportReporter,
)

DATASET_NAME = "bernabepuente/database-sql-instruction-dataset"
DATASET_SPLIT = "train"
SOURCE = DATASET_NAME
SOURCE_TYPE = "huggingface"
DATASET_VERSION = "v1"
OUTPUT_PATH = Path("datasets/curated/hf_import/database_sql_instruction.json")


def _load_raw_records() -> list[RawQuestionRecord]:

    adapter = HuggingFaceDatabaseAdapter()

    dataset = load_dataset(
        DATASET_NAME,
        split=DATASET_SPLIT,
    )

    records: list[RawQuestionRecord] = []

    for item in dataset:

        if not isinstance(item, dict):
            continue

        records.append(
            adapter.adapt(
                payload=item,
                source=SOURCE,
                source_type=SOURCE_TYPE,
                dataset_version=DATASET_VERSION,
            )
        )

    return records


def _export_curated_questions(
    questions: list[CuratedQuestion],
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = [question.model_dump(mode="json") for question in questions]

    output_path.write_text(
        json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:

    raw_records = _load_raw_records()

    orchestrator = MinimalIngestionOrchestrator()

    curated_questions = orchestrator.ingest(
        raw_records,
    )

    _export_curated_questions(
        curated_questions,
        OUTPUT_PATH,
    )

    reporter = CorpusImportReporter()

    reporter.print_summary(
        raw_count=len(raw_records),
        curated_questions=curated_questions,
        export_path=OUTPUT_PATH,
    )

    reporter.print_sample_questions(
        curated_questions=curated_questions,
        sample_size=10,
    )


if __name__ == "__main__":
    main()
