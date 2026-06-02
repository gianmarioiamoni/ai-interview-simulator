# scripts/question_corpus/import_backend_hf_dataset.py

import json
from pathlib import Path

from datasets import load_dataset

from domain.contracts.corpus.curated_question import CuratedQuestion
from services.question_ingestion.adapters.huggingface_backend_adapter import (
    HuggingFaceBackendAdapter,
)
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)

DATASET_NAME = "bernabepuente/backend-api-instruction-dataset"
DATASET_SPLIT = "train"
SOURCE = DATASET_NAME
SOURCE_TYPE = "huggingface"
DATASET_VERSION = "v1"
OUTPUT_PATH = Path("datasets/curated/hf_import/backend_api_instruction.json")


def _load_raw_records() -> list[RawQuestionRecord]:

    adapter = HuggingFaceBackendAdapter()

    dataset = load_dataset(
        DATASET_NAME,
        split=DATASET_SPLIT,
    )

    records = []

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

    print()
    print(f"RAW RECORDS:       {len(raw_records)}")
    print(f"CURATED QUESTIONS: {len(curated_questions)}")
    print(f"EXPORT PATH:       {OUTPUT_PATH}")
    print()
    print("FIRST 10 CURATED QUESTIONS")
    print()

    for question in curated_questions[:10]:

        print(f"id:         {question.id}")
        print(f"area:       {question.area.value}")
        print(f"role:       {question.role.value}")
        print(f"level:      {question.seniority.value}")
        print(f"difficulty: {question.difficulty}")
        print(f"source:     {question.source}")
        print(f"question:   {question.question}")
        print()


if __name__ == "__main__":
    main()
