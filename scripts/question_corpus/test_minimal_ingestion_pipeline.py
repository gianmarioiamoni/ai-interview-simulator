# scripts/question_corpus/test_minimal_ingestion_pipeline.py

from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.orchestration.minimal_ingestion_orchestrator import (
    MinimalIngestionOrchestrator,
)


SAMPLE_QUESTIONS = [
    {
        "text": "What is recursion and when would you use it?",
        "area": "technical_technical_knowledge",
        "role": "backend_engineer",
        "level": "junior",
        "difficulty": 2,
    },
    {
        "text": "Explain polymorphism in object-oriented programming.",
        "area": "technical_technical_knowledge",
    },
    {
        "text": "How would you design a URL shortener at scale?",
        "area": "technical_case_study",
        "role": "backend_engineer",
        "level": "senior",
        "difficulty": 5,
    },
    {
        "text": "Explain normalization and denormalization trade-offs in SQL databases.",
        "area": "technical_database",
    },
    {
        "text": "Implement a function to detect a cycle in a linked list.",
        "area": "technical_coding",
        "level": "mid",
    },
]


def _build_raw_records() -> list[RawQuestionRecord]:

    records: list[RawQuestionRecord] = []

    for index, sample in enumerate(SAMPLE_QUESTIONS, start=1):

        payload = dict(sample)

        records.append(
            RawQuestionRecord(
                source="minimal_ingestion_pilot",
                source_type="pilot_script",
                dataset_version="phase_4a",
                raw_payload=payload,
                canonical_payload=payload,
            ),
        )

    return records


def main() -> None:

    orchestrator = MinimalIngestionOrchestrator()

    curated_questions = orchestrator.ingest(
        _build_raw_records(),
    )

    print()
    print(f"CURATED QUESTIONS: {len(curated_questions)}")
    print()

    for question in curated_questions:

        print(f"id:         {question.id}")
        print(f"area:       {question.area.value}")
        print(f"level:      {question.seniority.value}")
        print(f"difficulty: {question.difficulty}")
        print(f"source:     {question.source}")
        print(f"question:   {question.question}")
        print()


if __name__ == "__main__":
    main()
