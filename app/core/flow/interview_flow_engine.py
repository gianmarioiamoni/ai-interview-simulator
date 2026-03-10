# app/core/flow/interview_flow_engine.py

import logging

from domain.contracts.question import QuestionType
from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer

from app.ui.controllers.interview_controller import InterviewController
from app.core.flow.interview_flow_state import InterviewFlowState
from app.core.evaluation.execution_score_policy import ExecutionScorePolicy
from services.execution_engine import ExecutionEngine


logger = logging.getLogger(__name__)


class InterviewFlowEngine:

    def __init__(self, controller: InterviewController):

        self._controller = controller
        self._execution_engine = ExecutionEngine()
        self._execution_score_policy = ExecutionScorePolicy()

    # =========================================================
    # START INTERVIEW
    # =========================================================

    def start(self, state: InterviewState):

        session_dto = self._controller.start_interview(state)

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "session": session_dto,
        }

    # =========================================================
    # PROCESS ANSWER (NEW CENTRAL PIPELINE)
    # =========================================================

    def process_answer(
        self,
        state: InterviewState,
        user_answer: str,
    ):

        current_question = state.questions[state.current_question_index]

        # ---------------------------------------------
        # Step 1 — Evaluate answer (LLM)
        # ---------------------------------------------

        session_dto, feedback, completed = self._controller.submit_answer(
            state,
            user_answer,
        )

        # ---------------------------------------------
        # Step 2 — Execute if coding/database question
        # ---------------------------------------------

        execution_error = None

        if current_question.type in [
            QuestionType.CODING,
            QuestionType.DATABASE,
        ]:

            answer = Answer(
                question_id=current_question.id,
                content=user_answer,
                attempt=1,
            )

            result = self._execution_engine.execute(
                current_question,
                user_answer,
            )

            state.execution_results.append(result)

            # -----------------------------------------
            # Step 3 — Apply execution score policy
            # -----------------------------------------

            if state.evaluations:

                last_eval = state.evaluations[-1]

                if last_eval.question_id == result.question_id:

                    updated = self._execution_score_policy.apply(
                        last_eval,
                        result,
                    )

                    state.evaluations[-1] = updated

                    logger.info(
                        f"Execution policy applied: "
                        f"{result.passed_tests}/{result.total_tests}"
                    )

            if not result.success:

                execution_error = result.error if result.error else "Unknown error"

        # ---------------------------------------------
        # Step 4 — Flow state
        # ---------------------------------------------

        if completed:

            return {
                "flow_state": InterviewFlowState.COMPLETION,
                "feedback": feedback,
                "session": session_dto,
                "execution_error": execution_error,
            }

        question = session_dto.current_question

        if question.question_type in [
            QuestionType.CODING,
            QuestionType.DATABASE,
        ]:

            return {
                "flow_state": InterviewFlowState.EXECUTION,
                "feedback": feedback,
                "session": session_dto,
                "execution_error": execution_error,
            }

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "feedback": feedback,
            "session": session_dto,
            "execution_error": execution_error,
        }

    # =========================================================
    # REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        return self._controller.generate_final_report(state)

    # =========================================================
    # ROUTER ACCESS
    # =========================================================

    @property
    def execution_engine(self):
        return self._execution_engine
