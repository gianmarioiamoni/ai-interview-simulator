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

        bundle = getattr(state, "last_feedback_bundle", None)

        if not bundle or not bundle.blocks:
            return ""

        blocks = bundle.blocks
        quality = bundle.overall_quality or "unknown"

        parts: list[str] = []

        # -----------------------------------------------------
        # HEADER (🔥 UX DIFFERENTIATED - MANTENUTO)
        # -----------------------------------------------------

        parts.append(FeedbackSection._build_header(quality))

        # -----------------------------------------------------
        # PRIORITIZE BLOCKS (🔥 NEW)
        # -----------------------------------------------------

        priority_titles = ["Summary", "Score"]

        priority_blocks = [b for b in blocks if b.title in priority_titles]
        other_blocks = [b for b in blocks if b.title not in priority_titles]

        ordered_blocks = priority_blocks + other_blocks

        # -----------------------------------------------------
        # RENDER ALL BLOCKS (ORDERED)
        # -----------------------------------------------------

        for block in ordered_blocks:

            # -------------------------------
            # TITLE
            # -------------------------------
            if block.title:
                parts.append(f"\n### {block.title}")

            # -------------------------------
            # CONTENT
            # -------------------------------
            if block.content:
                parts.append(block.content)

            # -------------------------------
            # SIGNALS
            # -------------------------------
            if block.signals:
                parts.append("\n#### 🔍 Issues")
                for s in block.signals:
                    parts.append(f"- {s.message}")

            # -------------------------------
            # LEARNING
            # -------------------------------
            if block.learning:
                parts.append("\n#### 💡 Suggestions")
                for l in block.learning:
                    parts.append(f"- {l.action}")

        # -----------------------------------------------------
        # AI HINT (TEMPORARY - verrà centralizzato step 3)
        # -----------------------------------------------------

        if result.ai_hint:
            parts.append("\n#### 🤖 Hint")
            parts.append(f"- {result.ai_hint}")

        return "\n".join(parts)

    # =========================================================
    # UX HEADER (INVARIATO)
    # =========================================================

    @staticmethod
    def _build_header(quality: str) -> str:

        if quality == "correct":
            return "### ✅ Correct Solution\nGreat job! All tests passed."

        if quality == "partial":
            return "### ⚠️ Partial Solution\nSome tests failed. You're close."

        if quality == "incorrect":
            return (
                "### ❌ Incorrect Solution\nThe solution needs significant improvement."
            )

        return "### ℹ️ Evaluation Result"

    # =========================================================
    # POLICY (INVARIATA)
    # =========================================================

    @staticmethod
    def _should_show(
        state: InterviewState,
        current_q,
    ) -> bool:

        if not current_q:
            return False

        return state.is_question_processed(current_q)
