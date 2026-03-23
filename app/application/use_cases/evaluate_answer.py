# app/application/use_cases/evaluate_answer.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from services.execution_engine import ExecutionEngine
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from services.ai_hint_engine.ai_hint_service import AIHintService

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.evaluation_decision import EvaluationDecision
from domain.contracts.ai_hint import AIHintInput
from domain.contracts.hint_level import HintLevel


class EvaluateAnswerUseCase:

    def __init__(self, llm):
        self.llm = llm
        self.engine = ExecutionEngine()
        self.hint_service = AIHintService()

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
            state = self._evaluate_execution(state, question, answer)

        # ---------------------------------------------------------
        # GENERATE AI HINT (SINGLE SOURCE OF TRUTH)
        # ---------------------------------------------------------

        result = state.get_result_for_question(question.id)
        if not result:
            return state

        attempts = state.attempts_by_question.get(question.id, 0)

        hint_level = self._resolve_hint_level(attempts)

        execution = result.execution

        error = execution.error if execution else None

        failed_tests = "None"
        if execution and execution.test_results:
            failed = [t for t in execution.test_results if t.status != "PASSED"]
            if failed:
                failed_tests = "\n".join(
                    [
                        f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                        for t in failed[:2]
                    ]
                )

        user_code = answer.content if answer else ""

        hint_input = AIHintInput(
            error=error,
            user_code=user_code[:1000],
            failed_tests=failed_tests,
            question=question.prompt,
            hint_level=hint_level,
        )

        try:
            ai_hint = self.hint_service.generate_hint(
                hint_input,
                level=hint_level.value,
            )
        except Exception:
            ai_hint = None

        updated = result.model_copy(
            update={
                "ai_hint": ai_hint,
                "hint_level": hint_level,
            }
        )

        state.results_by_question[question.id] = updated

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

        if result and result.execution:
            return state

        execution = self.engine.execute(
            question,
            answer.content,
        )

        state.register_execution(execution)

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

        state.register_evaluation(evaluation)

        return state

    def _resolve_hint_level(self, attempts: int) -> HintLevel:
        if attempts <= 1:
            return HintLevel.BASIC
        if attempts == 2:
            return HintLevel.TARGETED
        return HintLevel.SOLUTION