# app/graph/nodes/written_evaluation_node.py

from domain.contracts.interview_state import InterviewState

from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt

from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.feedback.evaluation_decision import EvaluationDecision
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import WRITTEN_EVALUATION
from infrastructure.config.evaluation import WRITTEN_PASS_THRESHOLD


class WrittenEvaluationNode:

    def __init__(self, llm):
        self._llm = llm

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.get_latest_answer_for_question(question.id)

        if question is None or answer is None:
            return state

        result = state.get_result_for_question(question.id)

        if result and result.evaluation is not None:
            return state

        prompt = build_evaluation_prompt(question, answer, role=state.role, seniority_level=state.seniority_level)

        with LLMOperationContext.scope(WRITTEN_EVALUATION):
            response = self._llm.invoke(prompt)

        try:
            decision = EvaluationDecision.model_validate_json(response.content)

            evaluation = QuestionEvaluation(
                question_id=question.id,
                score=decision.score,
                max_score=100,
                passed=decision.score >= WRITTEN_PASS_THRESHOLD,
                feedback=decision.feedback,
                strengths=list(getattr(decision, "strengths", []) or []),
                weaknesses=list(getattr(decision, "weaknesses", []) or []),
            )

        except Exception:
            evaluation = QuestionEvaluation(
                question_id=question.id,
                score=0,
                max_score=100,
                passed=False,
                feedback="Evaluation failed due to parsing error.",
                strengths=[],
                weaknesses=["Evaluation parsing failed"],
            )

        new_results = dict(state.results_by_question)

        if result is None:
            from domain.contracts.question.question_result import QuestionResult

            result = QuestionResult(question_id=question.id)

        result = result.model_copy(update={"evaluation": evaluation})
        new_results[question.id] = result

        return state.model_copy(update={"results_by_question": new_results})
