# app/ui/controllers/interview_controller.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from infrastructure.llm.llm_factory import get_llm

from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from app.core.logger import get_logger

from services.evaluation_engine import EvaluationEngine

from services.question_evaluation_service import QuestionEvaluationService
from services.interview_evaluation_service import InterviewEvaluationService


class InterviewController:

    def __init__(self, graph, mapper: InterviewStateMapper):

        self._graph = graph
        self._mapper = mapper

        self._evaluation_engine = EvaluationEngine()
        self._evaluation_service = InterviewEvaluationService(get_llm())

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
        state: InterviewState,
        user_answer: str,
    ) -> tuple[InterviewSessionDTO | None, str, bool]:

        current_question = state.questions[state.current_question_index]

        answer = Answer(
            question_id=current_question.id,
            content=user_answer,
            attempt=1,
        )

        state.answers.append(answer)

        # LLM evaluation
        question_eval = self._evaluation_engine.evaluate(
            question=current_question,
            answer_text=user_answer,
        )

        state.evaluations.append(question_eval)

        # Not last question
        if state.current_question_index < len(state.questions) - 1:

            state.current_question_index += 1

            session_dto = self._mapper.to_session_dto(state)

            return session_dto, question_eval.feedback, False

        # Last question
        state.progress = InterviewProgress.COMPLETED

        return None, question_eval.feedback, True

    # ---------------------------------------------------------
    # Generate Final Report
    # ---------------------------------------------------------

    def generate_final_report(self, state: InterviewState) -> FinalReportDTO:

        if state.final_evaluation is None:

            final_eval = self._evaluation_service.evaluate(
                per_question_evaluations=state.evaluations,
                questions=state.questions,
                interview_type=state.interview_type,
                role=state.role.type,
            )

            state.final_evaluation = final_eval

        return self._mapper.to_final_report_dto(state)
