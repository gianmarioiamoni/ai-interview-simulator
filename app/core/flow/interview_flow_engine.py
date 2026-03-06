# app/core/flow/interview_flow_engine.py
import logging 

from domain.contracts.question import QuestionType
from domain.contracts.interview_state import InterviewState

from app.ui.controllers.interview_controller import InterviewController

from app.core.flow.interview_flow_state import InterviewFlowState
from app.core.evaluation.execution_score_policy import ExecutionScorePolicy

from app.execution.execution_router import ExecutionRouter

logger = logging.getLogger(__name__)


class InterviewFlowEngine:

    def __init__(self, controller: InterviewController):

        self._controller = controller
        self._execution_router = ExecutionRouter()
        self._execution_score_policy = ExecutionScorePolicy()

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

        question = session_dto.current_question

        if question.question_type in [
            QuestionType.CODING,
            QuestionType.DATABASE,
        ]:

            return {
                "flow_state": InterviewFlowState.EXECUTION,
                "feedback": feedback,
                "session": session_dto,
            }

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "feedback": feedback,
            "session": session_dto,
        }

    # =========================================================
    # EXECUTE QUESTION
    # =========================================================

    def execute(
        self,
        state: InterviewState,
        session_dto,
    ):

        logger.info(f"Executing question {session_dto.current_question.question_id}")

        question_dto = session_dto.current_question

        # ---------------------------------------------------------
        # Retrieve domain question from state
        # ---------------------------------------------------------
        question = next(
            (q for q in state.questions if q.id == question_dto.question_id),
            None,
        )
        if not question:
            raise RuntimeError(f"Question not found: {question_dto.question_id}")

        answer = state.answers[-1].content

        result = self._execution_router.execute(
            question,
            answer,
        )

        state.execution_results.append(result)

        # ---------------------------------------------------------
        # Adjust evaluation using execution result
        # ---------------------------------------------------------
        if state.evaluations:
            evaluation = state.evaluations[-1]
            evaluation = self._execution_score_policy.apply(
                evaluation,
                result,
            )
            state.evaluations[-1] = evaluation

        if not result.success:

            return {
                "flow_state": InterviewFlowState.QUESTION,
                "session": session_dto,
                "execution_error": result.error if result.error else "Unknown error",
            }

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "session": session_dto,
        }

    # =========================================================
    # GENERATE REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        return self._controller.generate_final_report(state)

    # =========================================================
    # GENERATE REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        return self._controller.generate_final_report(state)
