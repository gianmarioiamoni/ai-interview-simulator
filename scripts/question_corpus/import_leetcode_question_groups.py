# scripts/question_corpus/import_leetcode_question_groups.py

import json
from pathlib import Path

from domain.contracts.corpus.curated_question import CuratedQuestion
from services.question_ingestion.adapters.leetcode_question_groups_adapter import (
    LeetcodeQuestionGroupsAdapter,
)
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)
from services.question_ingestion.reporting.corpus_import_reporter import (
    CorpusImportReporter,
)

DATASET_PATH = (
    "datasets/raw/github/tech-interview-handbook/apps/website/contents/"
    "_components/QuestionGroups.json"
)
SOURCE = "tech-interview-handbook/question-groups"
SOURCE_TYPE = "github"
DATASET_VERSION = "v1"
OUTPUT_PATH = Path(
    "datasets/curated/local_import/leetcode_question_groups.json",
)


def _load_raw_records() -> list[RawQuestionRecord]:

    adapter = LeetcodeQuestionGroupsAdapter()

    return adapter.adapt_file(
        dataset_path=DATASET_PATH,
        source=SOURCE,
        source_type=SOURCE_TYPE,
        dataset_version=DATASET_VERSION,
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

    rejected_count = len(raw_records) - len(curated_questions)

    reporter = CorpusImportReporter()

    reporter.print_summary(
        raw_count=len(raw_records),
        curated_questions=curated_questions,
        export_path=OUTPUT_PATH,
    )

    print(f"REJECTED QUESTIONS: {rejected_count}")
    print()

    reporter.print_sample_questions(
        curated_questions=curated_questions,
        sample_size=20,
    )


if __name__ == "__main__":
    main()
