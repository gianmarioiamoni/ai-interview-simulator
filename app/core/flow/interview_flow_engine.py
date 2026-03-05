# app/core/flow/interview_flow_engine.py

from domain.contracts.interview_state import InterviewState

from app.ui.controllers.interview_controller import InterviewController

from app.core.flow.interview_flow_state import InterviewFlowState


class InterviewFlowEngine:
    # High level orchestration engine managing the interview lifecycle.
    # Implements an explicit state machine controlling the flow
    # above the LangGraph execution layer.

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
    # HANDLE ANSWER
    # =========================================================

    def handle_answer(
        self,
        state: InterviewState,
        answer: str,
    ):

        session_dto, feedback, completed = self._controller.submit_answer(
            state,
            answer,
        )

        if completed:

            return {
                "flow_state": InterviewFlowState.COMPLETION,
                "feedback": feedback,
                "session": session_dto,
            }

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "feedback": feedback,
            "session": session_dto,
        }

    # =========================================================
    # GENERATE REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        report = self._controller.generate_final_report(state)

        return report
