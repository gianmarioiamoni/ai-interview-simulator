# tests/services/question_ingestion/test_seed_questions_import.py

from services.question_ingestion.loaders.json_dataset_loader import JSONDatasetLoader
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)


def test_seed_questions_import_pipeline() -> None:

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path="datasets/seed_questions.json",
        source="seed_questions",
    )

    orchestrator = MinimalIngestionOrchestrator()

    curated_questions = orchestrator.ingest(
        raw_records,
    )

    assert len(raw_records) == 40
    assert len(curated_questions) > 0
    assert all(question.source == "seed_questions" for question in curated_questions)
    assert all(question.question.strip() for question in curated_questions)
