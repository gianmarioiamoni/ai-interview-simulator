# app/ui/controllers/interview_controller.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from services.simple_llm_feedback_service import SimpleLLMFeedbackService
from app.core.logger import get_logger


class InterviewController:
    # Application-level controller.
    # Coordinates interview progression and maps domain state to UI DTOs.
    # Temporarily integrates simple LLM feedback per question.

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper
        self._feedback_service = SimpleLLMFeedbackService()
        self._logger = get_logger(__name__)

    # ---------------------------------------------------------
    # Start Interview
    # ---------------------------------------------------------

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:
        # Move state from SETUP to IN_PROGRESS via graph

        updated_state: InterviewState = self._graph.invoke(initial_state)

        self._logger.info("Interview started")

        return self._mapper.to_session_dto(updated_state)

    # ---------------------------------------------------------
    # Submit Answer
    # ---------------------------------------------------------

    def submit_answer(
        self,
        current_state: InterviewState,
        user_answer: str,
    ):
        # 1️⃣ Validate state consistency

        if not current_state.questions:
            return self._mapper.to_session_dto(current_state), "No question available."

        # 2️⃣ Retrieve current question

        index = current_state.current_question_index

        if index >= len(current_state.questions):
            index = len(current_state.questions) - 1

        question = current_state.questions[index]

        # 3️⃣ Compute attempt number for this question

        attempt_count = (
            sum(1 for a in current_state.answers if a.question_id == question.id) + 1
        )

        # 4️⃣ Create immutable Answer respecting domain contract

        answer = Answer(
            question_id=question.id,
            content=user_answer.strip(),
            attempt=attempt_count,
        )

        # Append to state (list is mutable even if model is frozen)
        current_state.answers.append(answer)

        # 5️⃣ Generate LLM feedback

        feedback = self._feedback_service.generate_feedback(
            question,
            user_answer,
        )

        # 6️⃣ Advance graph (move to next question or complete)

        updated_state: InterviewState = self._graph.invoke(current_state)

        # 7️⃣ If interview completed → return final report

        if updated_state.progress == InterviewProgress.COMPLETED:
            self._logger.info("Interview completed")

            report: FinalReportDTO = self._mapper.to_final_report_dto(updated_state)
            return report, feedback

        # 8️⃣ Otherwise → return next question session DTO

        session_dto: InterviewSessionDTO = self._mapper.to_session_dto(updated_state)
        return session_dto, feedback
