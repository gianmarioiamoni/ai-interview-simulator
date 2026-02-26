# app/ui/controllers/interview_controller.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from services.question_evaluation_service import QuestionEvaluationService
from app.core.logger import get_logger


class InterviewController:

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper
        self._question_eval_service = QuestionEvaluationService()
        self._logger = get_logger(__name__)

    # ---------------------------------------------------------
    # Start Interview
    # ---------------------------------------------------------

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:

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

        if not current_state.questions:
            return self._mapper.to_session_dto(current_state), "No question available."

        index = current_state.current_question_index

        if index >= len(current_state.questions):
            index = len(current_state.questions) - 1

        question = current_state.questions[index]

        # Compute attempt number
        attempt_count = (
            sum(1 for a in current_state.answers if a.question_id == question.id) + 1
        )

        answer = Answer(
            question_id=question.id,
            content=user_answer.strip(),
            attempt=attempt_count,
        )

        current_state.answers.append(answer)

        # Generate structured evaluation
        evaluation = self._question_eval_service.evaluate(
            question,
            user_answer,
        )

        current_state.evaluations.append(evaluation)

        feedback = evaluation.feedback

        # Advance graph
        updated_state: InterviewState = self._graph.invoke(current_state)

        # If interview completed → final report
        if updated_state.progress == InterviewProgress.COMPLETED:

            self._logger.info("Interview completed")

            report: FinalReportDTO = self._mapper.to_final_report_dto(updated_state)

            return report, feedback

        # Otherwise → next question
        session_dto: InterviewSessionDTO = self._mapper.to_session_dto(updated_state)

        return session_dto, feedback
