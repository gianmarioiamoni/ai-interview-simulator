# app/ui/controllers/interview_controller.py

from domain.contracts.answer import Answer
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_state import InterviewState
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from services.simple_llm_feedback_service import SimpleLLMFeedbackService


class InterviewController:

    def __init__(self, graph, mapper: InterviewStateMapper):
        self._graph = graph
        self._mapper = mapper
        self._feedback_service = SimpleLLMFeedbackService()

    def start_interview(self, initial_state: InterviewState) -> InterviewSessionDTO:
        updated_state: InterviewState = self._graph.invoke(initial_state)
        return self._mapper.to_session_dto(updated_state)

    def submit_answer(
        self,
        current_state: InterviewState,
        user_answer: str,
    ):

        # 1️⃣ get current question
        index = current_state.current_question_index
        question = current_state.questions[index]

        # 2️⃣ persist answer
        answer = Answer(
            question_id=question.id,
            content=user_answer,
        )
        current_state.answers.append(answer)

        # 3️⃣ LLM feedback
        feedback = self._feedback_service.generate_feedback(
            question,
            user_answer,
        )

        # 4️⃣ advance graph
        updated_state: InterviewState = self._graph.invoke(current_state)

        # 5️⃣ if completed → final report
        if updated_state.progress == InterviewProgress.COMPLETED:
            report = self._mapper.to_final_report_dto(updated_state)
            return report, feedback

        # 6️⃣ otherwise next question
        session_dto = self._mapper.to_session_dto(updated_state)
        return session_dto, feedback
