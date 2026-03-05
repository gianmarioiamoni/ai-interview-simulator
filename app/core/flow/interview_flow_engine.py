# app/core/flow/interview_flow_engine.py

from domain.contracts.question import QuestionType
from domain.contracts.interview_state import InterviewState

from app.ui.controllers.interview_controller import InterviewController

from app.core.flow.interview_flow_state import InterviewFlowState

from app.execution.execution_router import ExecutionRouter


class InterviewFlowEngine:
    # High level orchestration engine implementing
    # the interview state machine.
    # Responsible for controlling the lifecycle of the interview above LangGraph.

    def __init__(self, controller: InterviewController):

        self._controller = controller
        self._execution_router = ExecutionRouter()

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

        # ---------------------------------------------------------
        # EXECUTION branch
        # ---------------------------------------------------------

        if question.question_type in [
            QuestionType.CODING,
            QuestionType.DATABASE,
        ]:

            return {
                "flow_state": InterviewFlowState.EXECUTION,
                "feedback": feedback,
                "session": session_dto,
            }

        # ---------------------------------------------------------
        # Standard question
        # ---------------------------------------------------------

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

        question = session_dto.current_question

        answer = state.answers[-1].content

        result = self._execution_router.execute(
            question.question_type,
            answer,
        )

        # Persist execution result in state
        state.execution_results.append(result)

        if not result["success"]:

            return {
                "flow_state": InterviewFlowState.QUESTION,
                "session": session_dto,
                "execution_error": result["error"],
            }

        # -----------------------------
        # Execution success 
        # -----------------------------

        return {
            "flow_state": InterviewFlowState.QUESTION,
            "session": session_dto,
        }

    # =========================================================
    # GENERATE REPORT
    # =========================================================

    def generate_report(self, state: InterviewState):

        return self._controller.generate_final_report(state)
