# app/application/use_cases/evaluate_answer.py

# EvaluateAnswerUseCase
#
# - Handles answer evaluation pipeline
# - Written questions: LLM evaluation
# - Coding/DB questions: execution via LangGraph (ExecutionNode)
# - Hint generation remains centralized here (temporary, will move later)

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from services.execution_engine import ExecutionEngine
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from services.ai_hint_engine.ai_hint_service import AIHintService

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.ai_hint import AIHintInput
from domain.contracts.hint_level import HintLevel
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.test_execution_result import TestStatus

from app.graph.execution_graph import build_execution_graph


class EvaluateAnswerUseCase:

    def __init__(
        self,
        llm,
        execution_graph=None,
        hint_service=None,
    ):
        # Core dependencies
        self.llm = llm

        # Legacy (temporary, will be removed later)
        self.engine = ExecutionEngine()

        self.hint_service = hint_service or AIHintService()

        # Injectables (for testability)
        self.execution_graph = execution_graph or build_execution_graph(
            hint_service=self.hint_service
        )

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def execute(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        if question.type == QuestionType.WRITTEN:
            state = self._evaluate_written(state, question, answer)

        elif question.type in (QuestionType.CODING, QuestionType.DATABASE):
            result = state.get_result_for_question(question.id)
            if result and result.execution and result.evaluation and result.ai_hint:
                return state

            state = self._evaluate_execution(state, question, answer)

        return state

    # ---------------------------------------------------------
    # INTERNAL METHODS
    # ---------------------------------------------------------

    def _evaluate_written(self, state, question, answer):

        result = state.get_result_for_question(question.id)

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

        # Avoid re-execution
        if result and result.execution:
            return state

        # ---------------------------------------------------------
        # Execution via LangGraph
        # ---------------------------------------------------------

        graph_result = self.execution_graph.invoke(state)

        print("GRAPH RESULT TYPE:", type(graph_result))
        print("GRAPH RESULT RAW:", graph_result)

        # 🔥 ROBUST UNWRAP (final version)
        new_state = self._unwrap_graph_result(graph_result, fallback=state)

        if not isinstance(new_state, InterviewState):
            return state  # ultimate safety

        result = new_state.get_result_for_question(question.id)

        if not result or not result.execution:
            return new_state  # safe fallback

        execution = result.execution

        # ---------------------------------------------------------
        # Evaluation (unchanged logic)
        # ---------------------------------------------------------

        if execution.total_tests and execution.total_tests > 0:
            score = (execution.passed_tests / execution.total_tests) * 100
        else:
            score = 100 if execution.success else 0

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=score,
            max_score=100,
            passed=execution.success,
            feedback=execution.error or "Execution evaluated automatically.",
            strengths=[],
            weaknesses=[],
            passed_tests=execution.passed_tests,
            total_tests=execution.total_tests,
            execution_status=execution.status.value,
        )

        new_state.register_evaluation(evaluation)

        return new_state

    # ---------------------------------------------------------
    # GRAPH HELPER (CRITICAL)
    # ---------------------------------------------------------

    def _unwrap_graph_result(self, graph_result, fallback):

        # Case 1: already correct
        if isinstance(graph_result, InterviewState):
            return graph_result

        # Case 2: dict →  reconstruct InterviewState
        if isinstance(graph_result, dict):
            try:
                return InterviewState(**graph_result)
            except Exception:
                return fallback

        # Fallback safe
        return fallback

    # ---------------------------------------------------------

    def _resolve_hint_level(
        self,
        attempt: int,
        quality: str,
        execution: ExecutionResult,
    ) -> HintLevel:

        if execution and execution.error:
            if attempt == 1:
                return HintLevel.TARGETED
            return HintLevel.SOLUTION

        if quality == "incorrect":
            if attempt == 0:
                return HintLevel.NONE
            if attempt == 1:
                return HintLevel.BASIC
            if attempt == 2:
                return HintLevel.TARGETED
            return HintLevel.SOLUTION

        if quality == "partial":
            if attempt == 1:
                return HintLevel.BASIC
            return HintLevel.TARGETED

        if quality == "inefficient":
            return HintLevel.BASIC

        return HintLevel.NONE

    # ---------------------------------------------------------

    def _extract_execution_signals(self, execution: ExecutionResult) -> str:

        if not execution or not execution.test_results:
            return "None"

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]

        if not failed:
            return "None"

        return "\n".join(
            [
                f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                for t in failed[:2]
            ]
        )
