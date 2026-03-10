# app/core/flow/interview_flow_engine.py

import logging

from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer

from app.ui.controllers.interview_controller import InterviewController
from app.core.flow.interview_flow_state import InterviewFlowState


logger = logging.getLogger(__name__)


class InterviewFlowEngine:

    def __init__(self, controller: InterviewController):

        self._controller = controller

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
        # Step 1 — Register answer
        # -----------------------------------------------------

        answer = Answer(
            question_id=current_question.id,
            content=user_answer,
            attempt=1,
        )

        state.answers.append(answer)

        # -----------------------------------------------------
        # Step 2 — Run LangGraph
        # -----------------------------------------------------

        state = self._controller._graph.invoke(state)

        # -----------------------------------------------------
        # Step 3 — Build session DTO
        # -----------------------------------------------------

        session_dto = self._controller._mapper.to_session_dto(state)

        feedback = ""

        if state.evaluations:
            feedback = state.evaluations[-1].feedback

        completed = state.progress.value == "COMPLETED"

        # -----------------------------------------------------
        # Step 4 — Flow routing for UI
        # -----------------------------------------------------

        if completed:

            return {
                "flow_state": InterviewFlowState.COMPLETION,
                "feedback": feedback,
                "session": session_dto,
                "execution_error": None,
            }

        question = session_dto.current_question

        if question and question.question_type in ["coding", "database"]:

            return {
                "flow_state": InterviewFlowState.EXECUTION,
                "feedback": feedback,
                "session": session_dto,
                "execution_error": None,
            }

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "feedback": feedback,
            "session": session_dto,
            "execution_error": None,
        }

    # =========================================================
    # REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        return self._controller.generate_final_report(state)
