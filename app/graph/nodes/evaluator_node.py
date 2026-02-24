# app/graph/nodes/evaluator_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.evaluation import EvaluationResult
from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.question import Question

from infrastructure.llm.llm_factory import get_llm
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt


def evaluator_node(state: InterviewState) -> InterviewState:
    # Guard: nothing to evaluate
    if not state.answers:
        return state

    last_answer = state.answers[-1]

    # Retrieve related question
    question = next(
        (q for q in state.questions if q.id == last_answer.question_id), None
    )

    if question is None:
        return state

    # No evaluation for coding/sql (handled via execution engine)
    if question.type in ["coding", "sql"]:
        return state

    # Call LLM for evaluation
    llm = get_llm()

    response = llm.invoke(
        build_evaluation_prompt(question=question, answer=last_answer)
    )

    decision = EvaluationDecision.model_validate_json(response.content)

    # Create evaluation result
    evaluation = EvaluationResult(
        question_id=question.id, score=decision.score, feedback=decision.feedback
    )

    state.evaluations.append(evaluation)

    # Follow-up logic
    can_generate_followup = (
        decision.clarification_needed
        and state.follow_up_count < 2
        and not state.last_was_follow_up
        and question.type == "written"
    )

    if can_generate_followup and decision.follow_up_question:
        # Generate follow-up as new temporary question
        followup_question = Question(
            id=f"{question.id}_followup_{state.follow_up_count + 1}",
            content=decision.follow_up_question,
            type="written",
            is_follow_up=True,
        )

        state.questions.insert(state.current_question_index + 1, followup_question)

        state.current_question_id = followup_question.id
        state.follow_up_count += 1
        state.last_was_follow_up = True

        return state

    # No follow-up
    state.last_was_follow_up = False

    return state
