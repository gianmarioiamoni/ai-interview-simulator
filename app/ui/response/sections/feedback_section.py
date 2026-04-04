# app/ui/response/sections/feedback_section.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.quality import Quality


class FeedbackSection:

    @staticmethod
    def build(
        state: InterviewState,
    ) -> str:

        current_q = state.current_question
        if not FeedbackSection._should_show(state, current_q):
            return ""

        result = state.get_result_for_question(current_q.id)
        if not result:
            return ""

        bundle = state.last_feedback_bundle

        if not bundle or not bundle.blocks:
            return ""

        blocks = bundle.blocks
        quality = bundle.overall_quality

        parts: list[str] = []

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        parts.append(FeedbackSection._build_header(quality))

        # -----------------------------------------------------
        # PRIORITIZE BLOCKS
        # -----------------------------------------------------

        priority_titles = ["Summary", "Score"]

        priority_blocks = [b for b in blocks if b.title in priority_titles]
        other_blocks = [b for b in blocks if b.title not in priority_titles]

        ordered_blocks = priority_blocks + other_blocks

        # -----------------------------------------------------
        # RENDER BLOCKS
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
            # SIGNALS (🔥 FIX QUI)
            # -------------------------------
            if block.signals and block.severity in ["warning", "error"]:
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

        return "\n".join(parts)

    # =========================================================
    # UX HEADER
    # =========================================================

    @staticmethod
    def _build_header(quality: Quality) -> str:

        if quality == Quality.OPTIMAL:
            return "### 🏆 Optimal Solution\nExcellent performance and correctness."

        if quality == Quality.CORRECT:
            return "### ✅ Correct Solution\nGreat job! All tests passed."

        if quality == Quality.INEFFICIENT:
            return "### ⚠️ Inefficient Solution\nCorrect but performance can be improved."

        if quality == Quality.PARTIAL:
            return "### ⚠️ Partial Solution\nSome tests failed. You're close."

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
