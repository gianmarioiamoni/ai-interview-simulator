# app/application/use_cases/evaluate_answer.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from services.execution_engine import ExecutionEngine
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.evaluation_decision import EvaluationDecision


class EvaluateAnswerUseCase:

    def __init__(self, llm):
        self.llm = llm
        self.engine = ExecutionEngine()

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def execute(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        # ---------------------------------------------------------
        # WRITTEN QUESTION
        # ---------------------------------------------------------

        if question.type == QuestionType.WRITTEN:
            return self._evaluate_written(state, question, answer)

        # ---------------------------------------------------------
        # CODING / DATABASE
        # ---------------------------------------------------------

        if question.type in (QuestionType.CODING, QuestionType.DATABASE):
            return self._evaluate_execution(state, question, answer)

        return state

    # ---------------------------------------------------------
    # INTERNAL METHODS
    # ---------------------------------------------------------

    def _evaluate_written(self, state, question, answer):

        result = state.get_result_for_question(question.id)

        # Avoid double evaluation
        if result and result.evaluation:
            return state

        prompt = build_evaluation_prompt(question, answer)

        response = self.llm.invoke(prompt)

        try:
            decision = EvaluationDecision.model_validate_json(response.content)

            evaluation = QuestionEvaluation(
                question_id=question.id,
                score=decision.score,
                max_score=100,
                passed=decision.score >= 60,
                feedback=decision.feedback,
                strengths=getattr(decision, "strengths", []),
                weaknesses=getattr(decision, "weaknesses", []),
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

        state.register_evaluation(evaluation)

        return state

    # ---------------------------------------------------------

    def _evaluate_execution(self, state, question, answer):

        result = state.get_result_for_question(question.id)

        # Avoid double execution
        if result and result.execution:
            return state

        execution = self.engine.execute(
            question,
            answer.content,
        )

        state.register_execution(execution)

        return state
