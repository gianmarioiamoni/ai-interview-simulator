# services/humanizer/humanizer_service.py

from langchain_core.language_models.chat_models import BaseChatModel

from services.humanizer.builders.humanizer_prompt_builder import HumanizerPromptBuilder
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_output import HumanizerOutput
from services.humanizer.humanizer_policy_engine import HumanizerPolicyEngine
from services.humanizer.humanizer_response_parser import HumanizerResponseParser


class HumanizerService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        llm: BaseChatModel,
    ) -> None:

        self._llm = llm

        self._policy_engine = HumanizerPolicyEngine()

        self._prompt_builder = HumanizerPromptBuilder()

        self._parser = HumanizerResponseParser()

    # =====================================================
    # PUBLIC
    # =====================================================

    def humanize(
        self,
        input_data: HumanizerInput,
    ) -> HumanizerOutput:

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        decision = self._policy_engine.decide(
            input_data=input_data,
        )

        # -------------------------------------------------
        # PROMPT
        # -------------------------------------------------

        prompt = self._prompt_builder.build(
            input_data=input_data,
            decision=decision,
        )

        # -------------------------------------------------
        # LLM
        # -------------------------------------------------

        response = self._llm.invoke(prompt)

        content = response.content.strip()

        # -------------------------------------------------
        # PARSE
        # -------------------------------------------------

        return self._parser.parse(
            response=content,
        )
