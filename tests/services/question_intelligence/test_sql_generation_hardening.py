# tests/services/question_intelligence/test_sql_generation_hardening.py
"""
Phase 7E-G4 — SQL Generation Hardening Tests

Covers:
- Valid schema generates valid SQL
- Invalid column attempt triggers ValueError (enabling retry)
- Missing schema context graceful failure
- Retry path regenerates valid SQL after invalid-column failure
- Prompt hardening: schema summary includes types + foreign keys
- Prompt hardening: forbidden column names listed in execution rules
- Enrichment invalid column triggers retry path (returns None)
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.sql_engine.sql_executor import SQLExecutor

RETRIEVE_SQL_CANDIDATES = (
    "services.question_intelligence.pipelines.sql_question_pipeline."
    "retrieve_sql_candidates"
)

# ── valid SQL using real schema columns ───────────────────────────────────────

_VALID_SQL_JSON = json.dumps(
    [
        {
            "prompt": "List all employees with their department names.",
            "reference_query": (
                "SELECT e.name, d.name AS department "
                "FROM employees e "
                "JOIN departments d ON e.department_id = d.id"
            ),
            "test_cases": [
                {
                    "expected_query": (
                        "SELECT e.name, d.name FROM employees e "
                        "INNER JOIN departments d ON d.id = e.department_id"
                    ),
                    "ordered": False,
                },
                {
                    "expected_query": (
                        "SELECT employees.name, departments.name "
                        "FROM employees, departments "
                        "WHERE employees.department_id = departments.id"
                    ),
                    "ordered": False,
                },
            ],
        }
    ]
)

# ── SQL using hallucinated column 'employee_name' ─────────────────────────────

_INVALID_COLUMN_SQL_JSON = json.dumps(
    [
        {
            "prompt": "List all employee names.",
            "reference_query": "SELECT employee_name FROM employees",
            "test_cases": [
                {
                    "expected_query": "SELECT employee_name FROM employees ORDER BY employee_name",
                    "ordered": True,
                },
                {
                    "expected_query": "SELECT employee_name FROM employees",
                    "ordered": False,
                },
            ],
        }
    ]
)

# ── SQL using invalid table ───────────────────────────────────────────────────

_INVALID_TABLE_SQL_JSON = json.dumps(
    [
        {
            "prompt": "List all staff members.",
            "reference_query": "SELECT name FROM staff",
            "test_cases": [
                {"expected_query": "SELECT name FROM staff", "ordered": False},
                {"expected_query": "SELECT name FROM staff ORDER BY name", "ordered": True},
            ],
        }
    ]
)

# ── fallback valid SQL ────────────────────────────────────────────────────────

_FALLBACK_VALID_JSON = json.dumps(
    [
        {
            "prompt": "List all department names ordered alphabetically.",
            "reference_query": "SELECT name FROM departments ORDER BY name",
            "test_cases": [
                {
                    "expected_query": "SELECT name FROM departments ORDER BY name ASC",
                    "ordered": True,
                },
                {
                    "expected_query": "SELECT d.name FROM departments d ORDER BY d.name",
                    "ordered": True,
                },
            ],
        }
    ]
)


def _make_llm(*responses: str) -> MagicMock:
    llm = MagicMock()
    llm.invoke.side_effect = [MagicMock(content=r) for r in responses]
    return llm


def _assert_executable(question) -> None:
    execution = SQLExecutor().execute(
        question=question,
        query=question.reference_solution,
    )
    assert execution.success is True
    assert execution.passed_tests == execution.total_tests


# ── 1. Valid schema → generates valid SQL ─────────────────────────────────────


def test_valid_schema_generates_valid_sql() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    questions = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        n=1,
    )

    assert len(questions) == 1
    _assert_executable(questions[0])


# ── 2. Invalid column → ValueError raised (enables retry) ────────────────────


def test_invalid_column_raises_value_error() -> None:
    llm = _make_llm(_INVALID_COLUMN_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    with pytest.raises(ValueError, match="failed execution validation"):
        generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )


def test_invalid_table_raises_value_error() -> None:
    llm = _make_llm(_INVALID_TABLE_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    with pytest.raises(ValueError, match="failed execution validation"):
        generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )


# ── 3. Missing / malformed JSON → graceful failure ───────────────────────────


def test_missing_schema_graceful_failure_on_bad_json() -> None:
    llm = _make_llm("not valid json at all")
    generator = SQLQuestionGenerator(llm)

    with pytest.raises(ValueError, match="Invalid JSON"):
        generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )


def test_enrich_missing_schema_returns_none_on_bad_json() -> None:
    llm = _make_llm("not valid json at all")
    generator = SQLQuestionGenerator(llm)

    result = generator.enrich_from_prompt(
        seed_prompt="Write a query to get employee names.",
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
    )

    assert result is None


# ── 4. Retry path: invalid column first, valid SQL second ────────────────────


def test_retry_path_generates_valid_sql_after_invalid_column() -> None:
    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _make_llm(_INVALID_COLUMN_SQL_JSON, _FALLBACK_VALID_JSON)
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(RETRIEVE_SQL_CANDIDATES, return_value=[]):
        questions, _ = pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) == 1
    _assert_executable(questions[0])
    assert llm.invoke.call_count == 2


def test_retry_path_uses_both_attempts_and_succeeds() -> None:
    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _make_llm(_INVALID_COLUMN_SQL_JSON, _VALID_SQL_JSON)
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(RETRIEVE_SQL_CANDIDATES, return_value=[]):
        questions, _ = pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert llm.invoke.call_count == 2


# ── 5. Enrich invalid column → returns None (triggers next candidate) ─────────


def test_enrich_invalid_column_returns_none() -> None:
    llm = _make_llm(_INVALID_COLUMN_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    result = generator.enrich_from_prompt(
        seed_prompt="Write a query to get employee names with department.",
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
    )

    assert result is None


# ── 6. Prompt hardening: schema summary includes column types ─────────────────


def test_prompt_includes_column_types_in_schema_summary() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    generator.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

    prompt_text = llm.invoke.call_args[0][0]
    assert "INTEGER" in prompt_text
    assert "TEXT" in prompt_text


def test_prompt_includes_foreign_key_definitions() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    generator.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

    prompt_text = llm.invoke.call_args[0][0]
    assert "department_id" in prompt_text
    assert "departments.id" in prompt_text


def test_prompt_includes_forbidden_column_warning() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    generator.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

    prompt_text = llm.invoke.call_args[0][0]
    assert "employee_name" in prompt_text
    assert "FORBIDDEN" in prompt_text or "NOT" in prompt_text


def test_generation_prompt_explicitly_names_employee_column() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    generator.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

    prompt_text = llm.invoke.call_args[0][0]
    assert 'column for an employee\'s name is "name"' in prompt_text


def test_enrichment_prompt_explicitly_names_employee_column() -> None:
    llm = _make_llm(_VALID_SQL_JSON)
    generator = SQLQuestionGenerator(llm)

    generator.enrich_from_prompt(
        seed_prompt="Write a query to get employee names.",
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
    )

    prompt_text = llm.invoke.call_args[0][0]
    assert 'column for an employee\'s name is "name"' in prompt_text


# ── 7. Partial success: mix of valid and invalid items ────────────────────────


def test_partial_valid_items_returns_only_valid_ones() -> None:
    mixed_json = json.dumps(
        [
            {
                "prompt": "Bad question using invented column.",
                "reference_query": "SELECT employee_name FROM employees",
                "test_cases": [
                    {"expected_query": "SELECT employee_name FROM employees", "ordered": False},
                    {"expected_query": "SELECT employee_name FROM employees", "ordered": False},
                ],
            },
            {
                "prompt": "List all department names.",
                "reference_query": "SELECT name FROM departments",
                "test_cases": [
                    {"expected_query": "SELECT name FROM departments", "ordered": False},
                    {"expected_query": "SELECT d.name FROM departments d", "ordered": False},
                ],
            },
        ]
    )

    llm = _make_llm(mixed_json)
    generator = SQLQuestionGenerator(llm)

    questions = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        n=2,
    )

    assert len(questions) == 1
    assert "department" in questions[0].prompt.lower()
    _assert_executable(questions[0])
