# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.humanizer_service import HumanizerService
from services.interview_memory.interview_memory_updater import InterviewMemoryUpdater
from infrastructure.config.settings import settings


def _build_display_prompt(question) -> str:
    """Prepend schema block for DATABASE questions that carry db_schema."""
    if question.type == QuestionType.DATABASE and question.db_schema:
        schema_block = (
            "**Database Schema**\n\n"
            f"```sql\n{question.db_schema.strip()}\n```\n\n"
        )
        return schema_block + question.prompt
    return question.prompt


def build_question_node(llm):

    humanizer_service = HumanizerService(
        llm=llm,
        follow_up_enabled=settings.humanizer_follow_up_enabled,
    )

    memory_updater = InterviewMemoryUpdater()

    def question_node(state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        # ---------------------------------------------------------
        # Prevent double processing
        # ---------------------------------------------------------

        if state.current_question_index < len(state.chat_history):
            return state

        # ---------------------------------------------------------
        # Humanizer disabled
        # ---------------------------------------------------------

        if not state.enable_humanizer:

            new_history = state.chat_history + [_build_display_prompt(question)]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                }
            )

        # ---------------------------------------------------------
        # Non written questions
        # ---------------------------------------------------------

        if question.type != QuestionType.WRITTEN:

            new_history = state.chat_history + [_build_display_prompt(question)]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                }
            )

        # ---------------------------------------------------------
        # INPUT DATA
        # ---------------------------------------------------------

        last_answer = None

        last_score = None

        if state.answers:

            last_answer = state.answers[-1].content

        if state.last_feedback_bundle:

            last_score = state.last_feedback_bundle.overall_quality.rank()

        input_data = HumanizerInput(
            current_question=question,
            language=state.language,
            chat_history=state.chat_history,
            last_answer=last_answer,
            last_answer_score=last_score,
            follow_up_count=state.follow_up_count,
            last_turn_was_follow_up=(state.last_humanizer_follow_up),
        )

        # ---------------------------------------------------------
        # HUMANIZE
        # ---------------------------------------------------------

        output = humanizer_service.humanize(
            input_data=input_data,
        )

        # ---------------------------------------------------------
        # FOLLOW-UP TRACKING
        # ---------------------------------------------------------

        is_follow_up = output.decision == HumanizerDecision.FOLLOW_UP

        follow_up_count = (
            state.follow_up_count + 1 if is_follow_up else state.follow_up_count
        )

        # ---------------------------------------------------------
        # UPDATE HISTORY
        # ---------------------------------------------------------

        new_history = state.chat_history + [output.message]

        updated_memory = memory_updater.update_after_question(
            memory=state.memory_context,
            question=question,
        )

        return state.model_copy(
            update={
                "chat_history": new_history,
                "follow_up_count": follow_up_count,
                "last_humanizer_follow_up": (is_follow_up),
                "memory_context": updated_memory,
            }
        )

    return question_node
