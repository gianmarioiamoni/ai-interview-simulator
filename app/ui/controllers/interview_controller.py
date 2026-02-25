# app/ui/controllers/interview_controller.py

from typing import Union

from domain.contracts.interview_state import InterviewState
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.core.logger import get_logger
from services.simple_llm_feedback_service import SimpleLLMFeedbackService


class InterviewController:

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper
        self._feedback_service = SimpleLLMFeedbackService()

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:
        updated_state: InterviewState = self._graph.invoke(initial_state)

        logger = get_logger(__name__)
        logger.info("Interview started")

        return self._mapper.to_session_dto(updated_state)

    def submit_answer(
        self,
        current_state: InterviewState,
        user_answer: str,
    ) -> str:

        if not current_state.questions:
            return "No question available."

        index = current_state.current_question_index

        if index >= len(current_state.questions):
            index = 0

        question = current_state.questions[index]

        feedback = self._feedback_service.generate_feedback(
            question,
            user_answer,
        )

        return feedback
