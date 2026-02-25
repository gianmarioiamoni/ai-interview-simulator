# app/ui/controllers/interview_controller.py

from domain.contracts.answer import Answer
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_state import InterviewState


def submit_answer(
    self,
    current_state: InterviewState,
    user_answer: str,
):

    # 1️⃣ Current question
    index = current_state.current_question_index
    question = current_state.questions[index]

    # 2️⃣ Compute attempt number
    attempt_count = (
        sum(1 for a in current_state.answers if a.question_id == question.id) + 1
    )

    # 3️⃣ Create immutable Answer respecting domain contract
    answer = Answer(
        question_id=question.id,
        content=user_answer.strip(),
        attempt=attempt_count,
    )

    # Since state.answers is a mutable list, we append
    current_state.answers.append(answer)

    # 4️⃣ Generate LLM feedback
    feedback = self._feedback_service.generate_feedback(
        question,
        user_answer,
    )

    # 5️⃣ Advance graph
    updated_state: InterviewState = self._graph.invoke(current_state)

    # 6️⃣ If interview completed → final report
    if updated_state.progress == InterviewProgress.COMPLETED:
        report = self._mapper.to_final_report_dto(updated_state)
        return report, feedback

    # 7️⃣ Otherwise → next question
    session_dto = self._mapper.to_session_dto(updated_state)
    return session_dto, feedback
