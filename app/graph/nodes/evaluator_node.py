# app/graph/nodes/evaluator_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.evaluation import EvaluationResult
from domain.contracts.evaluation_decision import EvaluationDecision
from services.prompt_builders.evaluation_prompt_builder import (
    build_evaluation_prompt,
)
from app.ports.llm_port import LLMPort


def build_evaluator_node(llm: LLMPort):

    def evaluator_node(state: InterviewState) -> InterviewState:

        if not state.answers:
            return state

        last_answer = state.answers[-1]

        question = next(
            (q for q in state.questions if q.id == last_answer.question_id), None
        )

        if question is None:
            return state

        if question.type in ["coding", "sql"]:
            state.last_was_follow_up = False
            return state

        already_evaluated = any(
            ev.question_id == question.id for ev in state.evaluations
        )

        if already_evaluated:
            return state

        prompt = build_evaluation_prompt(question, last_answer)

        response = llm.invoke(prompt)

        decision = EvaluationDecision.model_validate_json(response.content)

        evaluation = EvaluationResult(
            question_id=question.id,
            score=decision.score,
            feedback=decision.feedback,
        )

        state.evaluations.append(evaluation)

        can_generate_followup = (
            decision.clarification_needed
            and state.follow_up_count < 2
            and not state.last_was_follow_up
            and decision.follow_up_question
        )

        if can_generate_followup:
            from domain.contracts.question import Question

            followup_question = Question(
                id=f"{question.id}_followup_{state.follow_up_count + 1}",
                content=decision.follow_up_question,
                type="written",
                is_follow_up=True,
            )

            state.questions.insert(
                state.current_question_index + 1,
                followup_question,
            )

            state.current_question_id = followup_question.id
            state.follow_up_count += 1
            state.last_was_follow_up = True

            return state

        state.last_was_follow_up = False
        return state

    return evaluator_node
