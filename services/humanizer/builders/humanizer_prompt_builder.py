# services/humanizer/builders/humanizer_prompt_builder.py

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from services.humanizer.contracts.humanizer_decision import (
    HumanizerDecision,
)
from services.humanizer.contracts.humanizer_input import (
    HumanizerInput,
)


class HumanizerPromptBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        input_data: HumanizerInput,
        decision: HumanizerDecision,
    ) -> str:

        template = PromptLoader.load("transformation/humanizer_v2.txt")

        history_snippet = self._build_history(
            input_data=input_data,
        )

        context = {
            "decision": decision.value,
            "question": input_data.current_question.prompt,
            "language": input_data.language,
            "history": history_snippet,
            "previous_question": (input_data.previous_question or ""),
            "previous_answer": (input_data.previous_answer or ""),
            "previous_score": (
                input_data.previous_score
                if input_data.previous_score is not None
                else ""
            ),
            "previous_area": (input_data.previous_area or ""),
            "follow_up_count": input_data.follow_up_count,
            "last_answer": input_data.last_answer or "",
            "last_answer_score": input_data.last_answer_score or 0,
        }

        return PromptRenderer.render(
            template,
            context,
        )

    # =====================================================
    # PRIVATE
    # =====================================================

    def _build_history(
        self,
        input_data: HumanizerInput,
    ) -> str:

        if not input_data.chat_history:

            return ""

        return "\n".join(input_data.chat_history[-5:])
