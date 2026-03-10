# app/graph/nodes/evaluate_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from domain.contracts.evaluation_decision import EvaluationDecision


def build_evaluate_node(llm):

    def evaluate_node(state: InterviewState) -> InterviewState:

        last_answer = state.last_answer
        question = state.current_question

        if not last_answer or not question:
            return state

        if question.type != QuestionType.WRITTEN:
            return state

        # avoid duplicate evaluation
        if any(ev.question_id == question.id for ev in state.evaluations):
            return state

        prompt = build_evaluation_prompt(question, last_answer)

        response = llm.invoke(prompt)

        try:
            decision = EvaluationDecision.model_validate_json(response.content)
        except Exception:
            return state

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=decision.score,
            max_score=100,
            passed=decision.score >= 60,
            feedback=decision.feedback,
            strengths=getattr(decision, "strengths", []),
            weaknesses=getattr(decision, "weaknesses", []),
        )

        new_evaluations = state.evaluations + [evaluation]

        return state.model_copy(update={"evaluations": new_evaluations})

    return evaluate_node
