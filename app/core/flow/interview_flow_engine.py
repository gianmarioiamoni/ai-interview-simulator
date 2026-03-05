# app/core/flow/interview_flow_engine.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress

from app.ui.controllers.interview_controller import InterviewController


class InterviewFlowEngine:
    # Orchestrates the interview flow above the graph and controller.
    # Responsible for high-level interview lifecycle management.

    def __init__(self, controller: InterviewController):

        self._controller = controller

    # ---------------------------------------------------------
    # Start interview
    # ---------------------------------------------------------

    def start(self, initial_state: InterviewState):

        session_dto = self._controller.start_interview(initial_state)

        return session_dto

    # ---------------------------------------------------------
    # Handle answer
    # ---------------------------------------------------------

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
                "type": "completion",
                "feedback": feedback,
                "state": state,
            }

        return {
            "type": "question",
            "feedback": feedback,
            "session": session_dto,
            "state": state,
        }

    # ---------------------------------------------------------
    # Generate report
    # ---------------------------------------------------------

    def generate_report(self, state: InterviewState):

        report = self._controller.generate_final_report(state)

        return report
