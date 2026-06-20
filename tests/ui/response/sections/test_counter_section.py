# tests/ui/response/sections/test_counter_section.py

from app.ui.response.sections.counter_section import CounterSection
from tests.factories.interview_state_factory import build_interview_state, build_question
from domain.contracts.interview.answer import Answer


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def _state_with_answers(n_answers: int):
    question = build_question(qid="q1")
    answers = [
        Answer(question_id="q1", content=f"answer {i}", attempt=i + 1)
        for i in range(n_answers)
    ]
    return build_interview_state(questions=[question], answers=answers)


# ---------------------------------------------------------
# CounterSection.build — renders exactly the value passed in
# ---------------------------------------------------------


def test_counter_renders_1_of_3():
    state = _state_with_answers(0)
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Attempt 1 / 3" in result


def test_counter_renders_2_of_3():
    state = _state_with_answers(0)
    result = CounterSection.build(state, state.current_question, attempts=2, max_attempts=3)
    assert "Attempt 2 / 3" in result


def test_counter_renders_3_of_3():
    state = _state_with_answers(0)
    result = CounterSection.build(state, state.current_question, attempts=3, max_attempts=3)
    assert "Attempt 3 / 3" in result


def test_counter_no_plus_one_bias():
    """CounterSection must NOT apply +1 internally."""
    state = _state_with_answers(0)
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Attempt 2" not in result


# ---------------------------------------------------------
# display_attempt computation (mirrors ui_response_builder logic)
# ---------------------------------------------------------


def _compute_display_attempt(attempts: int, is_feedback_mode: bool) -> int:
    return attempts if is_feedback_mode else (attempts + 1)


def test_question_mode_attempts_0_display_is_1():
    assert _compute_display_attempt(0, is_feedback_mode=False) == 1


def test_question_mode_attempts_1_display_is_2():
    assert _compute_display_attempt(1, is_feedback_mode=False) == 2


def test_feedback_mode_attempts_1_display_is_1():
    assert _compute_display_attempt(1, is_feedback_mode=True) == 1


def test_feedback_mode_attempts_2_display_is_2():
    assert _compute_display_attempt(2, is_feedback_mode=True) == 2


def test_feedback_mode_attempts_3_display_is_3():
    assert _compute_display_attempt(3, is_feedback_mode=True) == 3


# ---------------------------------------------------------
# B1: adaptive counter uses len(planned_areas)
# ---------------------------------------------------------


def _adaptive_state(planned_area_count: int, current_index: int = 0):
    from domain.contracts.interview.interview_area import InterviewArea

    questions = [build_question(qid=f"q{i}") for i in range(current_index + 1)]
    state = build_interview_state(
        questions=questions,
        current_question_index=current_index,
    )
    planned_areas = [InterviewArea.TECH_CODING.value] * planned_area_count
    return state.model_copy(
        update={
            "adaptive_interview_enabled": True,
            "planned_areas": planned_areas,
        }
    )


def test_counter_adaptive_q1_shows_planned_total():
    """B1: first question of a 20-question adaptive interview shows 1/20, not 1/1."""
    state = _adaptive_state(planned_area_count=20, current_index=0)
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Question 1 / 20" in result


def test_counter_adaptive_mid_interview_shows_planned_total():
    """B1: 5th question with 20 planned shows 5/20, not 5/5."""
    state = _adaptive_state(planned_area_count=20, current_index=4)
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Question 5 / 20" in result


def test_counter_batch_mode_uses_len_questions():
    """B1 regression: batch mode (adaptive disabled) uses len(questions)."""
    questions = [build_question(qid=f"q{i}") for i in range(5)]
    state = build_interview_state(questions=questions, current_question_index=0)
    state = state.model_copy(update={"adaptive_interview_enabled": False})
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Question 1 / 5" in result


def test_counter_adaptive_no_planned_areas_falls_back_to_questions():
    """B1 edge case: adaptive enabled but planned_areas empty → falls back to len(questions)."""
    questions = [build_question(qid="q1")]
    state = build_interview_state(questions=questions)
    state = state.model_copy(
        update={"adaptive_interview_enabled": True, "planned_areas": []}
    )
    result = CounterSection.build(state, state.current_question, attempts=1, max_attempts=3)
    assert "Question 1 / 1" in result
