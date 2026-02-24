# Evaluator node
#
# Responsibility: evaluates written answers and optionally generates follow-up questions.

from app.ports.llm_port import LLMPort
from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType, Question
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.question_evaluation import QuestionEvaluation
import json


def build_evaluator_node(llm: LLMPort):

    def evaluator_node(state: InterviewState) -> InterviewState:

        if not state.answers:
            return state

        if not state.current_question_id:
            return state

        answered_current = any(
            a.question_id == state.current_question_id for a in state.answers
        )

        if not answered_current:
            return state

        last_answer = state.answers[-1]

        if state.current_question_id != last_answer.question_id:
            return state

        if any(ev.question_id == last_answer.question_id for ev in state.evaluations):
            return state

        question = next(
            (q for q in state.questions if q.id == last_answer.question_id),
            None,
        )

        if question is None:
            return state

        if question.type != QuestionType.WRITTEN:
            return state.model_copy(
                update={
                    "last_was_follow_up": False,
                    "current_question_id": None,
                    "current_question_index": state.current_question_index + 1,
                }
            )

        prompt = build_evaluation_prompt(question, last_answer)
        response = llm.invoke(prompt)

        try:
            decision = EvaluationDecision.model_validate_json(response.content)
        except Exception:
            # Hard failure fallback
            return state

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=decision.score,
            max_score=100,
            passed=decision.score >= 60,
            feedback=decision.feedback,
            strengths=decision.strengths,
            weaknesses=decision.weaknesses,
        )

        new_evaluations = state.evaluations + [evaluation]

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

            new_questions = (
                state.questions[: state.current_question_index + 1]
                + [followup_question]
                + state.questions[state.current_question_index + 1 :]
            )

            return state.model_copy(
                update={
                    "evaluations": new_evaluations,
                    "questions": new_questions,
                    "current_question_index": state.current_question_index + 1,
                    "current_question_id": followup_question.id,
                    "follow_up_count": state.follow_up_count + 1,
                    "last_was_follow_up": True,
                    "awaiting_user_input": False,
                }
            )

        return state.model_copy(
            update={
                "evaluations": new_evaluations,
                "last_was_follow_up": False,
                "current_question_id": None,
                "current_question_index": state.current_question_index + 1,
                "awaiting_user_input": False,
            }
        )

    return evaluator_node
