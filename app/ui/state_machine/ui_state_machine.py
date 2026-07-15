# app/ui/state_machine/ui_state_machine.py

from app.ui.replay.replay_context import ReplayContext
from app.ui.ui_state import UIState
from domain.contracts.interview_state import InterviewState

from app.core.logger import get_logger

logger = get_logger(__name__)


class UIStateMachine:
    @staticmethod
    def resolve(
        state: InterviewState | None,
        replay_context: ReplayContext | None = None,
    ) -> UIState:
        # REPLAY — takes precedence when the UI-layer signal is active (I-C10-01).
        if replay_context is not None and replay_context.is_active:
            logger.debug("resolved UI state: REPLAY")
            return UIState.REPLAY

        if state is None:
            return UIState.SETUP

        # REPORT
        if state.report is not None:
            logger.debug("resolved UI state: REPORT")
            return UIState.REPORT

        # COMPLETION
        if state.is_completed:
            logger.debug("resolved UI state: COMPLETION")
            return UIState.COMPLETION

        # SETUP
        if not state.current_question:
            logger.debug("resolved UI state: SETUP")
            return UIState.SETUP

        # PROCESSING
        if state.is_processing:
            logger.debug("resolved UI state: PROCESSING")
            return UIState.PROCESSING

        # FEEDBACK
        if (
            not state.is_processing
            and state.allowed_actions
            and state.last_feedback_bundle is not None
        ):
            logger.debug("resolved UI state: FEEDBACK")
            return UIState.FEEDBACK

        # DEFAULT = QUESTION
        logger.debug("resolved UI state: QUESTION")
        return UIState.QUESTION
