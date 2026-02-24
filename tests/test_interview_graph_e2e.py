# tests/test_interview_graph_e2e.py

from app.graph.interview_graph import build_interview_graph
from domain.contracts.interview_state import InterviewState
from domain.contracts.question import Question
from domain.contracts.interview_progress import InterviewProgress

from tests.fakes.fake_llm import FakeLLM


def test_interview_graph_single_written_question():
    from domain.contracts.question import QuestionType

    # LLM responses:
    # 1 → humanizer output
    # 2 → evaluator JSON
    fake_llm = FakeLLM(
        [
            "Let's start with this question.",
            """
        {
            "score": 80,
            "feedback": "Good understanding but missing depth.",
            "clarification_needed": false,
            "follow_up_question": null
        }
        """,
        ]
    )

    graph = build_interview_graph(fake_llm)

    question = Question(
        id="q1",
        area="backend",
        type=QuestionType.WRITTEN,
        prompt="Explain what a REST API is.",
        difficulty=3,
    )

    state = InterviewState(
        interview_id="int_1",
        role="Backend Engineer",
        company="TestCorp",
        questions=[question],
        current_question_id="q1",
    )

    # Simulate candidate answer before evaluator
    from domain.contracts.answer import Answer

    state.answers.append(Answer(question_id="q1", content="A REST API is ...", attempt=1))

    result = graph.invoke(state)
    final_state = InterviewState.model_validate(result)

    assert final_state.total_score == 80
    assert final_state.progress == InterviewProgress.COMPLETED
    assert len(final_state.evaluations) == 1
    assert final_state.follow_up_count == 0


def test_followup_generated_once():
    from domain.contracts.question import QuestionType

    fake_llm = FakeLLM(
        [
            # First invoke: humanizer for question 1
            "Conversational framing.",
            # First invoke: evaluator for question 1 (creates follow-up)
            """
        {
            "score": 60,
            "feedback": "Partially correct.",
            "clarification_needed": true,
            "follow_up_question": "Can you elaborate on HTTP methods?"
        }
        """,
            # First invoke: humanizer for follow-up question (created in first invoke)
            "Follow-up conversational framing.",
            # Second invoke: evaluator for follow-up question  
            """
        {
            "score": 75,
            "feedback": "Better clarification.",
            "clarification_needed": false,
            "follow_up_question": null
        }
        """,
        ]
    )

    graph = build_interview_graph(fake_llm)

    question = Question(
        id="q1",
        area="backend",
        type=QuestionType.WRITTEN,
        prompt="Explain REST.",
        difficulty=3,
    )

    state = InterviewState(
        interview_id="int_2",
        role="Backend Engineer",
        company="TestCorp",
        questions=[question],
        current_question_id="q1",
    )

    from domain.contracts.answer import Answer

    state.answers.append(Answer(question_id="q1", content="REST is ...", attempt=1))

    result_dict = graph.invoke(state)
    result = InterviewState(**result_dict)

    # Now answer follow-up
    followup_question = result.questions[1]

    result.answers.append(
        Answer(question_id=followup_question.id, content="HTTP methods are...", attempt=1)
    )

    final_dict = graph.invoke(result)
    final_state = InterviewState(**final_dict)

    assert final_state.follow_up_count == 1
    # total_score is the average of all evaluations: (60 + 75) / 2 = 67.5
    assert final_state.total_score == 67.5
    assert final_state.progress.name == "COMPLETED"
