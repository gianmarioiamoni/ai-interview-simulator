# scripts/question_corpus/import_ak_interview_hf_dataset.py

import json
from pathlib import Path

from datasets import load_dataset

from domain.contracts.corpus.curated_question import CuratedQuestion
from services.question_ingestion.adapters.huggingface_ak_interview_adapter import (
    HuggingFaceAkInterviewAdapter,
)
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)
from services.question_ingestion.reporting.corpus_import_reporter import (
    CorpusImportReporter,
)

DATASET_NAME = "akshar2109/ak_interview"
DATASET_SPLITS = ("train", "test")
SOURCE = DATASET_NAME
SOURCE_TYPE = "huggingface"
DATASET_VERSION = "v1"
OUTPUT_PATH = Path("datasets/curated/hf_import/ak_interview.json")


def _load_raw_records() -> list[RawQuestionRecord]:

    adapter = HuggingFaceAkInterviewAdapter()

    records: list[RawQuestionRecord] = []

    for split in DATASET_SPLITS:

        dataset = load_dataset(
            DATASET_NAME,
            split=split,
        )

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
