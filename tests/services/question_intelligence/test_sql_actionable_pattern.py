# tests/services/question_intelligence/test_sql_actionable_pattern.py

from unittest.mock import MagicMock

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
)
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator


def _is_actionable(text: str) -> bool:

    return SQLQuestionPipeline(
        retrieval_service=MagicMock(),
        sql_generator=MagicMock(),
    )._is_actionable_sql_prompt(text)


def test_indexing_question_becomes_actionable() -> None:

    assert _is_actionable("What is indexing in a database?")


def test_normalization_question_becomes_actionable() -> None:

    assert _is_actionable("What is database normalization?")


def test_transaction_question_becomes_actionable() -> None:

    assert _is_actionable("Explain transaction isolation levels in PostgreSQL.")


def test_view_question_remains_rejected() -> None:

    assert not _is_actionable("What is a view in SQL?")


def test_architecture_question_remains_rejected() -> None:

    assert not _is_actionable("What is database replication?")


def test_excluded_keywords_do_not_alone_open_gate() -> None:

    assert not _is_actionable("What is a cursor in SQL?")
    assert not _is_actionable("What is a NoSQL database?")
    assert not _is_actionable("Explain row-level locking in databases.")
    assert not _is_actionable("How does database sharding work?")


def test_enrichment_prompt_includes_sandbox_constraints() -> None:

    llm = MagicMock()
    generator = SQLQuestionGenerator(llm)

    generator.enrich_from_prompt(
        seed_prompt="What is indexing in a database?",
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
    )

    prompt = llm.invoke.call_args[0][0]

    assert "single SELECT only" in prompt
    assert "Do NOT use CREATE" in prompt
    assert "VIEW" in prompt
    assert "TRIGGER" in prompt
    assert "multi-statement" in prompt.lower()
