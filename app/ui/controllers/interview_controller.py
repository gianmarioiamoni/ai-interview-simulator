# app/ui/controllers/interview_controller.py

from typing import Union

from domain.contracts.interview_state import InterviewState
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.core.logger import get_logger
from services.simple_llm_feedback_service import SimpleLLMFeedbackService


class InterviewController:

    # Application-level controller.
    # Coordinates LangGraph execution and maps domain state to UI DTOs.

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper
        self._feedback_service = SimpleLLMFeedbackService()

    # ---------------------------------------------------------
    # Start Interview
    # ---------------------------------------------------------

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:
        # Starts the interview by invoking the graph with initial state.

        updated_state: InterviewState = self._graph.invoke(initial_state)

        logger = get_logger(__name__)
        logger.info("Interview started")

        return self._mapper.to_session_dto(updated_state)

    # ---------------------------------------------------------
    # Submit Answer
    # ---------------------------------------------------------

    # def submit_answer(
    #     self,
    #     current_state: InterviewState,
    #     user_answer: str,
    # #) -> Union[InterviewSessionDTO, FinalReportDTO]:
    # ) -> str:
    #     # Continues the interview flow.

    #     updated_state: InterviewState = self._graph.invoke(current_state)

    #     if updated_state.progress.name == "COMPLETED":
    #         return self._mapper.to_final_report_dto(updated_state)

    #     return self._mapper.to_session_dto(updated_state)
    # ---------------------------------------------------------
# Submit Answer
# ---------------------------------------------------------


def submit_answer(
    self,
    current_state: InterviewState,
    user_answer: str,
) -> str:
    # Minimal real LLM integration.
    # Graph is temporarily bypassed.
    # Generates simple textual feedback for the current question.

    if not current_state.questions:
        return "No question available."

    # Use current_question_index as pointer
    index = current_state.current_question_index

    if index >= len(current_state.questions):
        index = 0

    question = current_state.questions[index]

    feedback = self._feedback_service.generate_feedback(
        question,
        user_answer,
    )

    return feedback
