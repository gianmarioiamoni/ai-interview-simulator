# tests/services/question_ingestion/test_huggingface_database_adapter.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_ingestion.adapters.huggingface_database_adapter import (
    DATABASE_AREA,
    DATABASE_LEVEL,
    DATABASE_ROLE,
    HuggingFaceDatabaseAdapter,
)


def test_adapt_maps_instruction_to_text_with_explicit_metadata() -> None:
    adapter = HuggingFaceDatabaseAdapter()

    record = adapter.adapt(
        payload={
            "instruction": (
                "Explain the difference between a primary key and a unique index in PostgreSQL."
            ),
            "input": "",
            "output": "Detailed answer...",
            "thought": "Reasoning...",
        },
        source="bernabepuente/database-sql-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == (
        "Explain the difference between a primary key and a unique index in PostgreSQL."
    )
    assert record.canonical_payload["area"] == DATABASE_AREA
    assert record.canonical_payload["role"] == DATABASE_ROLE
    assert record.canonical_payload["level"] == DATABASE_LEVEL
    assert InterviewArea(record.canonical_payload["area"]) == InterviewArea.TECH_DATABASE
    assert RoleType(record.canonical_payload["role"]) == RoleType.BACKEND_ENGINEER
    assert SeniorityLevel(record.canonical_payload["level"]) == SeniorityLevel.MID
    assert record.source == "bernabepuente/database-sql-instruction-dataset"
    assert record.source_type == "huggingface"
    assert record.dataset_version == "v1"


def test_adapt_strips_instruction_whitespace() -> None:
    adapter = HuggingFaceDatabaseAdapter()

    record = adapter.adapt(
        payload={
            "instruction": "  What is the difference between WHERE and HAVING in PostgreSQL?  ",
        },
        source="bernabepuente/database-sql-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == (
        "What is the difference between WHERE and HAVING in PostgreSQL?"
    )


def test_adapt_preserves_full_raw_payload() -> None:
    adapter = HuggingFaceDatabaseAdapter()

    payload = {
        "instruction": "Explain the concept of indexing in PostgreSQL and provide an example.",
        "input": "users table",
        "output": "response body",
        "thought": "chain of thought",
    }

    record = adapter.adapt(
        payload=payload,
        source="bernabepuente/database-sql-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.raw_payload == payload
