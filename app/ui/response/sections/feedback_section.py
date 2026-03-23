# app/ui/response/sections/feedback_section.py

from domain.contracts.interview_state import InterviewState

from app.ui.presenters.result_presenter import ResultPresenter


class FeedbackSection:

    @staticmethod
    def build(
        state: InterviewState,
        presenter: ResultPresenter,
    ) -> str:

        current_q = state.current_question

        if not FeedbackSection._should_show(state, current_q):
            return ""

        result = state.get_result_for_question(current_q.id)

        if not result:
            return ""

        vm = presenter.present(
            state,
            result,
            current_q.prompt,
        )

        return vm.feedback_markdown

    # =========================================================
    # POLICY
    # =========================================================

    @staticmethod
    def _should_show(
        state: InterviewState,
        current_q,
    ) -> bool:

        if not current_q:
            return False

        return state.is_question_processed(current_q)
