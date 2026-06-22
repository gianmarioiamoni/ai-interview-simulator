# tests/ui/response/sections/test_display_section.py

import pytest

from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.execution.coding_test_case import CodingTestCase

from app.ui.response.sections.display_section import DisplaySection
from app.ui.ui_state import UIState

from tests.factories.interview_state_factory import build_interview_state


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

_SCHEMA = "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER);"
_PROMPT = "Write a query to list all employees."


def _make_question(
    qtype: QuestionType,
    *,
    db_schema: str | None = None,
    prompt: str = _PROMPT,
    qid: str = "q1",
) -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_DATABASE if qtype == QuestionType.DATABASE else InterviewArea.TECH_CODING,
        type=qtype,
        prompt=prompt,
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=db_schema,
    )


def _build(question: Question) -> dict:
    state = build_interview_state(questions=[question], answers=[])
    return DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)


# ---------------------------------------------------------
# DATABASE QUESTION WITH SCHEMA
# ---------------------------------------------------------


def test_database_question_with_schema_renders_schema_before_prompt():
    question = _make_question(QuestionType.DATABASE, db_schema=_SCHEMA)
    result = _build(question)

    db_text = result["database_display"]

    assert "### Database Schema" in db_text
    assert _SCHEMA.strip() in db_text
    assert "### Question" in db_text
    assert _PROMPT in db_text

    schema_pos = db_text.index("### Database Schema")
    question_pos = db_text.index("### Question")
    assert schema_pos < question_pos


def test_database_question_with_schema_wraps_in_sql_code_block():
    question = _make_question(QuestionType.DATABASE, db_schema=_SCHEMA)
    result = _build(question)

    db_text = result["database_display"]

    assert "```sql" in db_text
    assert "```" in db_text


def test_database_question_with_schema_does_not_bleed_into_other_panels():
    question = _make_question(QuestionType.DATABASE, db_schema=_SCHEMA)
    result = _build(question)

    assert result["written_display"] == ""
    assert result["coding_display"] == ""
    assert "### Database Schema" in result["database_display"]


# ---------------------------------------------------------
# DATABASE QUESTION WITHOUT SCHEMA
# ---------------------------------------------------------


def test_database_question_without_schema_renders_only_prompt():
    question = _make_question(QuestionType.DATABASE, db_schema=None)
    result = _build(question)

    db_text = result["database_display"]

    assert "### Database Schema" not in db_text
    assert "### Question" in db_text
    assert _PROMPT in db_text


def test_database_question_empty_schema_does_not_render_schema_block():
    question = _make_question(QuestionType.DATABASE, db_schema="")
    result = _build(question)

    assert "### Database Schema" not in result["database_display"]


# ---------------------------------------------------------
# WRITTEN QUESTION UNCHANGED
# ---------------------------------------------------------


def test_written_question_does_not_render_schema_block():
    question = Question(
        id="w1",
        area=InterviewArea.TECH_BACKGROUND,
        type=QuestionType.WRITTEN,
        prompt="Explain REST vs GraphQL.",
        difficulty=QuestionDifficulty.MEDIUM,
        db_schema=_SCHEMA,  # schema present but type is WRITTEN
    )
    state = build_interview_state(questions=[question], answers=[])
    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    assert "### Database Schema" not in result["written_display"]
    assert "Explain REST vs GraphQL." in result["written_display"]
    assert result["database_display"] == ""
    assert result["coding_display"] == ""


# ---------------------------------------------------------
# CODING QUESTION UNCHANGED
# ---------------------------------------------------------


def test_coding_question_does_not_render_schema_block():
    question = _make_question(QuestionType.CODING, db_schema=_SCHEMA)
    result = _build(question)

    assert "### Database Schema" not in result["coding_display"]
    assert _PROMPT in result["coding_display"]
    assert result["database_display"] == ""
    assert result["written_display"] == ""


# ---------------------------------------------------------
# HUMANIZER: question_display_text preferred over question.prompt
# ---------------------------------------------------------


def test_display_section_prefers_question_display_text_when_set():
    question = _make_question(QuestionType.WRITTEN)
    state = build_interview_state(questions=[question], answers=[])
    humanized = "So, building on what you mentioned earlier — walk me through REST."
    state = state.model_copy(update={"question_display_text": humanized})

    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    assert humanized in result["written_display"]
    assert _PROMPT not in result["written_display"]


def test_display_section_falls_back_to_question_prompt_when_display_text_is_none():
    question = _make_question(QuestionType.WRITTEN)
    state = build_interview_state(questions=[question], answers=[])
    state = state.model_copy(update={"question_display_text": None})

    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    assert _PROMPT in result["written_display"]


def test_display_section_coding_unaffected_by_humanizer_display_text():
    question = _make_question(QuestionType.CODING)
    state = build_interview_state(questions=[question], answers=[])
    state = state.model_copy(update={"question_display_text": "Humanized text"})

    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    assert "Humanized text" in result["coding_display"]
    assert result["written_display"] == ""


def test_display_section_database_schema_rendered_once_when_display_text_is_raw_prompt():
    """H2: question_node stores raw prompt; DisplaySection adds schema block exactly once."""
    question = _make_question(QuestionType.DATABASE, db_schema=_SCHEMA)
    # Simulate what question_node now stores: raw prompt only
    state = build_interview_state(questions=[question], answers=[])
    state = state.model_copy(update={"question_display_text": question.prompt})

    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    db_text = result["database_display"]
    schema_count = db_text.count("### Database Schema")
    assert schema_count == 1, f"Schema block rendered {schema_count} times"
    assert _PROMPT in db_text


# ---------------------------------------------------------
# CODING CONTRACT BLOCK
# ---------------------------------------------------------


def _make_coding_question(
    *,
    coding_spec: CodingSpec | None = None,
    visible_tests: list[CodingTestCase] | None = None,
    prompt: str = _PROMPT,
    qid: str = "q1",
) -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt=prompt,
        difficulty=QuestionDifficulty.MEDIUM,
        coding_spec=coding_spec,
        visible_tests=visible_tests or [],
    )


def test_coding_contract_block_shown_when_coding_spec_present():
    spec = CodingSpec(entrypoint="two_sum", parameters=["nums", "target"])
    question = _make_coding_question(coding_spec=spec)
    result = _build(question)

    text = result["coding_display"]
    assert "### Execution Contract" in text
    assert "def two_sum(nums, target)" in text
    assert "Exact equality" in text


def test_coding_contract_block_absent_when_coding_spec_is_none():
    question = _make_coding_question(coding_spec=None)
    result = _build(question)

    assert "### Execution Contract" not in result["coding_display"]


def test_coding_contract_block_absent_for_non_coding_question():
    spec = CodingSpec(entrypoint="solve", parameters=["x"])
    question = Question(
        id="w1",
        area=InterviewArea.TECH_BACKGROUND,
        type=QuestionType.WRITTEN,
        prompt=_PROMPT,
        difficulty=QuestionDifficulty.MEDIUM,
        coding_spec=spec,
    )
    state = build_interview_state(questions=[question], answers=[])
    result = DisplaySection.build(state, question, UIState.QUESTION, has_previous_answer=False)

    assert "### Execution Contract" not in result["written_display"]


def test_coding_examples_rendered_from_visible_tests():
    spec = CodingSpec(entrypoint="two_sum", parameters=["nums", "target"])
    tests = [
        CodingTestCase(args=[[2, 7, 11, 15], 9], expected=[0, 1]),
        CodingTestCase(args=[[3, 2, 4], 6], expected=[1, 2]),
    ]
    question = _make_coding_question(coding_spec=spec, visible_tests=tests)
    result = _build(question)

    text = result["coding_display"]
    assert "### Examples" in text
    assert "Example 1" in text
    assert "Example 2" in text
    assert "nums=" in text
    assert "target=" in text
    assert "[0, 1]" in text


def test_coding_examples_at_most_two_visible_tests():
    spec = CodingSpec(entrypoint="solve", parameters=["x"])
    tests = [
        CodingTestCase(args=[1], expected=2),
        CodingTestCase(args=[2], expected=4),
        CodingTestCase(args=[3], expected=6),
    ]
    question = _make_coding_question(coding_spec=spec, visible_tests=tests)
    result = _build(question)

    text = result["coding_display"]
    assert "Example 1" in text
    assert "Example 2" in text
    assert "Example 3" not in text


def test_coding_examples_absent_when_visible_tests_empty():
    spec = CodingSpec(entrypoint="solve", parameters=["x"])
    question = _make_coding_question(coding_spec=spec, visible_tests=[])
    result = _build(question)

    text = result["coding_display"]
    assert "### Execution Contract" in text
    assert "### Examples" not in text


def test_coding_contract_class_method_rendering():
    spec = CodingSpec(
        type="class_method",
        entrypoint="LRUCache",
        method_name="get",
        parameters=["key"],
    )
    question = _make_coding_question(coding_spec=spec)
    result = _build(question)

    text = result["coding_display"]
    assert "class LRUCache" in text
    assert "def get(self, key)" in text
