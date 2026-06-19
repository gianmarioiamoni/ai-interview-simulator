# tests/services/test_sql_executor.py

from domain.contracts.execution.execution_result import (
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.execution.execution_test_result import (
    TestStatus as ExecutionTestStatus,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
    SQLTestCase,
)
from services.sql_engine.sql_executor import SQLExecutor


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

SCHEMA = """
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    salary INTEGER NOT NULL
);
"""

SEED = """
INSERT INTO employees (id, name, salary) VALUES (1, 'Alice', 90000);
INSERT INTO employees (id, name, salary) VALUES (2, 'Bob', 70000);
INSERT INTO employees (id, name, salary) VALUES (3, 'Carol', 85000);
"""


def build_sql_question(
    *,
    schema: str = SCHEMA,
    seed: str = SEED,
    tests: list[SQLTestCase] | None = None,
) -> Question:

    return Question(
        id="q1",
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.DATABASE,
        prompt="Select the names of employees earning more than 80000.",
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=schema,
        db_seed_data=seed,
        sql_test_cases=tests
        or [
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name",
            )
        ],
    )


# ---------------------------------------------------------
# SUCCESSFUL EXECUTION
# ---------------------------------------------------------


def test_successful_query_execution():

    executor = SQLExecutor()
    question = build_sql_question()

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name",
    )

    assert result.success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.execution_type == ExecutionType.DATABASE
    assert result.passed_tests == 1
    assert result.total_tests == 1
    assert result.test_results[0].status == ExecutionTestStatus.PASSED


def test_unordered_comparison_accepts_different_row_order():

    executor = SQLExecutor()

    question = build_sql_question(
        tests=[
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name ASC",
                ordered=False,
            )
        ],
    )

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name DESC",
    )

    assert result.success is True
    assert result.test_results[0].status == ExecutionTestStatus.PASSED


# ---------------------------------------------------------
# EXECUTION FAILURES
# ---------------------------------------------------------


def test_failed_validation_wrong_rows():

    executor = SQLExecutor()
    question = build_sql_question()

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary < 80000",
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.passed_tests == 0
    assert result.total_tests == 1
    assert result.test_results[0].status == ExecutionTestStatus.FAILED
    assert result.error == "Test execution failed"


def test_partial_pass_with_multiple_tests():

    executor = SQLExecutor()

    question = build_sql_question(
        tests=[
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name",
            ),
            SQLTestCase(
                id="t2",
                expected_query="SELECT name FROM employees ORDER BY name",
            ),
        ],
    )

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name",
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.passed_tests == 1
    assert result.total_tests == 2


def test_no_test_cases_means_failure():

    executor = SQLExecutor()
    question = build_sql_question(tests=[])
    question = question.model_copy(update={"sql_test_cases": []})

    result = executor.execute(question, "SELECT 1")

    assert result.success is False
    assert result.total_tests == 0


# ---------------------------------------------------------
# MALFORMED SUBMISSIONS
# ---------------------------------------------------------


def test_sql_syntax_error_marks_test_as_error():

    executor = SQLExecutor()
    question = build_sql_question()

    result = executor.execute(question, "SELEC name FROM employees")

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.test_results[0].status == ExecutionTestStatus.ERROR
    assert "syntax" in result.test_results[0].error.lower()


def test_runtime_error_table_not_found():

    executor = SQLExecutor()
    question = build_sql_question()

    result = executor.execute(question, "SELECT * FROM non_existing_table")

    assert result.success is False
    assert result.test_results[0].status == ExecutionTestStatus.ERROR
    assert "no such table" in result.test_results[0].error.lower()


# ---------------------------------------------------------
# RUNTIME EXCEPTIONS
# ---------------------------------------------------------


def test_broken_schema_triggers_runtime_error():

    executor = SQLExecutor()
    question = build_sql_question(schema="CREATE TABLE broken (")

    result = executor.execute(question, "SELECT 1")

    assert result.success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.error is not None
    assert result.total_tests == 0


# ---------------------------------------------------------
# ORDERING REGRESSION: Question.expected_ordered propagation
# ---------------------------------------------------------


def test_case_a_unordered_question_accepts_different_row_order():
    """Case A: same rows, different order, expected_ordered=False → PASS."""

    executor = SQLExecutor()

    question = Question(
        id="q_case_a",
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.DATABASE,
        prompt="Select employee names.",
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=SCHEMA,
        db_seed_data=SEED,
        expected_ordered=False,
        sql_test_cases=[
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name ASC",
            )
        ],
    )

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name DESC",
    )

    assert result.success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.passed_tests == 1
    assert result.test_results[0].status == ExecutionTestStatus.PASSED


def test_case_b_ordered_question_fails_on_different_row_order():
    """Case B: same rows, different order, expected_ordered=True → FAIL."""

    executor = SQLExecutor()

    question = Question(
        id="q_case_b",
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.DATABASE,
        prompt="Select employee names.",
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=SCHEMA,
        db_seed_data=SEED,
        expected_ordered=True,
        sql_test_cases=[
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name ASC",
            )
        ],
    )

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name DESC",
    )

    assert result.success is False
    assert result.status == ExecutionStatus.FAILED_TESTS
    assert result.passed_tests == 0
    assert result.test_results[0].status == ExecutionTestStatus.FAILED


def test_per_case_ordered_overrides_question_expected_ordered():
    """Per-test ordered=True overrides Question.expected_ordered=False."""

    executor = SQLExecutor()

    question = Question(
        id="q_override",
        area=InterviewArea.TECH_DATABASE,
        type=QuestionType.DATABASE,
        prompt="Select employee names.",
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=SCHEMA,
        db_seed_data=SEED,
        expected_ordered=False,
        sql_test_cases=[
            SQLTestCase(
                id="t1",
                expected_query="SELECT name FROM employees WHERE salary > 80000 ORDER BY name ASC",
                ordered=True,
            )
        ],
    )

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name DESC",
    )

    assert result.success is False
    assert result.test_results[0].status == ExecutionTestStatus.FAILED


# ---------------------------------------------------------
# RESULT FORMATTING
# ---------------------------------------------------------


def test_result_formatting_contains_timing_and_ids():

    executor = SQLExecutor()
    question = build_sql_question()

    result = executor.execute(
        question,
        "SELECT name FROM employees WHERE salary > 80000 ORDER BY name",
    )

    assert result.question_id == "q1"
    assert result.execution_time_ms is not None
    assert result.execution_time_ms >= 0
    assert result.test_results[0].expected is not None
    assert result.test_results[0].actual is not None
