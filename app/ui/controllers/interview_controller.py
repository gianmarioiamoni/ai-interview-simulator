# app/ui/controllers/interview_controller.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from infrastructure.llm.llm_factory import get_llm

from app.ui.dto import final_report_dto
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from app.core.logger import get_logger

from services.question_evaluation_service import QuestionEvaluationService
from services.interview_evaluation_service import InterviewEvaluationService


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

    def submit_answer(self, state: InterviewState, user_answer: str):

        # 1️⃣ Retrieve current question
        current_question = state.questions[state.current_question_index]

        # 2️⃣ Save answer
        answer = Answer(
            question_id=current_question.id,
            content=user_answer,
            attempt=1,
        )
        state.answers.append(answer)

        # 3️⃣ Generate QuestionEvaluation
        question_eval = self._question_eval_service.evaluate(
            question=current_question,
            answer_text=user_answer,
        )
        state.evaluations.append(question_eval)

        # 4️⃣ If not last question → advance to next question
        if state.current_question_index < len(state.questions) - 1:

            state.current_question_index += 1

            session_dto = self._mapper.to_session_dto(state)

            return session_dto, question_eval.feedback

        # 5️⃣ If last question → complete interview
        state.progress = InterviewProgress.COMPLETED

        final_eval = self._interview_eval_service.evaluate(state.evaluations)
        state.final_evaluation = final_eval
        state.progress = InterviewProgress.COMPLETED

        final_report = self._mapper.to_final_report_dto(state)

        return final_report, question_eval.feedback

