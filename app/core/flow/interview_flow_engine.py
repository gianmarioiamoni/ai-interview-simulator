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
    # PROCESS ANSWER
    # =========================================================

    def process_answer(
        self,
        state: InterviewState,
        user_answer: str,
    ):

        current_question = state.current_question
        if not current_question:
            raise RuntimeError("No current question available in InterviewState")

        # -----------------------------------------------------
        # Step 1 — Register answer in state
        # -----------------------------------------------------

        answer = Answer(
            question_id=current_question.id,
            content=user_answer,
            attempt=1,
        )

        state.answers.append(answer)

        # -----------------------------------------------------
        # Step 2 — Run LangGraph pipeline
        # -----------------------------------------------------

        updated_state = self._controller._graph.invoke(state)

        # LangGraph works in-place but we keep explicit reference
        state = updated_state

        session_dto = self._controller._mapper.to_session_dto(state)

        feedback = ""

        if state.evaluations:
            last_eval = state.evaluations[-1]
            feedback = last_eval.feedback

        completed = state.progress.value == "COMPLETED"

        # -----------------------------------------------------
        # Step 3 — Execute if coding/database question
        # -----------------------------------------------------

        execution_error = None

        if current_question.type in [
            QuestionType.CODING,
            QuestionType.DATABASE,
        ]:

            result = self._execution_engine.execute(
                current_question,
                user_answer,
            )

            state.execution_results.append(result)

            # ---------------------------------------------
            # Apply execution score policy
            # ---------------------------------------------

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

        # -----------------------------------------------------
        # Step 4 — Flow state routing
        # -----------------------------------------------------

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
