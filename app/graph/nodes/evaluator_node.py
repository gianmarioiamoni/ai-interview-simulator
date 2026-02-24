# app/graph/nodes/evaluator_node.py

# Evaluator node
#
# This node is responsible for evaluating the answer of the candidate.
# It is used to evaluate the answer of the candidate and to generate a follow-up question if needed.
#
# Responsability: evaluates the answer of the candidate and generates a follow-up question if needed.

from app.ports.llm_port import LLMPort
from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.evaluation import EvaluationResult
from domain.contracts.question import Question

def build_evaluator_node(llm: LLMPort):

    def evaluator_node(state: InterviewState) -> InterviewState:

        if not state.answers:
            return state

        # If we are waiting for an answer to the current question, do nothing
        if state.current_question_id:
            answered_current = any(
            a.question_id == state.current_question_id for a in state.answers
        )
        if not answered_current:
            return state

        last_answer = state.answers[-1]

        # If the current_question_id does not match the last answer,
        # we are waiting for a new answer -> do nothing
        if state.current_question_id and state.current_question_id != last_answer.question_id:
            return state

        # Avoid double evaluation
        if any(ev.question_id == last_answer.question_id for ev in state.evaluations):
            return state

        question = next(
            (q for q in state.questions if q.id == last_answer.question_id),
            None,
        )

        if question is None:
            return state

        if question.type != QuestionType.WRITTEN:
            state.last_was_follow_up = False
            state.current_question_id = None
            state.current_question_index += 1
            return state

        prompt = build_evaluation_prompt(question, last_answer)
        response = llm.invoke(prompt)

        decision = EvaluationDecision.model_validate_json(response.content)

        evaluation = EvaluationResult(
            question_id=question.id,
            score=decision.score,
            max_score=100,
            passed=decision.score >= 60,
            feedback=decision.feedback,
        )

        state.evaluations.append(evaluation)
        state.awaiting_user_input = False

        can_generate_followup = (
            decision.clarification_needed
            and state.follow_up_count < 2
            and not state.last_was_follow_up
            and decision.follow_up_question
        )

        if can_generate_followup:

            followup_question = Question(
                id=f"{question.id}_followup_{state.follow_up_count + 1}",
                area=question.area,
                type=QuestionType.WRITTEN,
                prompt=decision.follow_up_question,
                difficulty=question.difficulty,
            )

            insert_index = state.current_question_index + 1

            state.questions.insert(
                state.current_question_index + 1,
                followup_question,
            )

            state.current_question_index = insert_index
            state.current_question_id = followup_question.id
            state.follow_up_count += 1
            state.last_was_follow_up = True

            return state

        state.last_was_follow_up = False
        state.current_question_id = None

        state.current_question_index += 1

        if state.current_question_index >= len(state.questions):
            state.current_question_id = None

        return state

    return evaluator_node
