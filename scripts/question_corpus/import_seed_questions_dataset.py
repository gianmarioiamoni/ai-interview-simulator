# scripts/question_corpus/import_seed_questions_dataset.py

import json
from pathlib import Path

from domain.contracts.corpus.curated_question import CuratedQuestion
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.loaders.json_dataset_loader import JSONDatasetLoader
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)
from services.question_ingestion.reporting.corpus_import_reporter import (
    CorpusImportReporter,
)

DATASET_PATH = "datasets/seed_questions.json"
SOURCE = "seed_questions"
OUTPUT_PATH = Path("datasets/curated/local_import/seed_questions.json")


def _load_raw_records() -> list[RawQuestionRecord]:

    loader = JSONDatasetLoader()

    return loader.load(
        dataset_path=DATASET_PATH,
        source=SOURCE,
    )


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
