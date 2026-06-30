# services/humanizer/humanizer_service.py

from langchain_core.language_models.chat_models import BaseChatModel

from services.humanizer.builders.humanizer_prompt_builder import HumanizerPromptBuilder
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_output import HumanizerOutput
from services.humanizer.humanizer_policy_engine import HumanizerPolicyEngine
from services.humanizer.humanizer_response_parser import HumanizerResponseParser
from services.humanizer.follow_up.follow_up_prompt_builder import FollowUpPromptBuilder
from services.humanizer.follow_up.follow_up_prompt_input import FollowUpPromptInput
from services.humanizer.follow_up.follow_up_parser import FollowUpParser
from services.humanizer.follow_up.follow_up_output import FollowUpOutput
from services.humanizer.follow_up.follow_up_parse_error import FollowUpParseError
from services.humanizer.guards.follow_up_guard_result import FollowUpGuardResult
from infrastructure.config.settings import Settings


class HumanizerService:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        llm: BaseChatModel,
        follow_up_enabled: bool = False,
    ) -> None:

        self._llm = llm

        self._policy_engine = HumanizerPolicyEngine(follow_up_enabled=follow_up_enabled)

        self._prompt_builder = HumanizerPromptBuilder()

        self._parser = HumanizerResponseParser()

        self._follow_up_prompt_builder = FollowUpPromptBuilder()

        self._follow_up_parser = FollowUpParser()

    # =====================================================
    # PUBLIC
    # =====================================================

    def humanize(
        self,
        input_data: HumanizerInput,
    ) -> tuple[HumanizerDecision, HumanizerOutput]:
        """Return (policy_decision, llm_output). Callers must use policy_decision
        for follow_up_count tracking — never output.decision."""

        # -------------------------------------------------
        # DECISION (policy-owned)
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

        output = self._parser.parse(
            response=content,
        )

        return decision, output

    def generate_follow_up(
        self,
        *,
        prompt_input: FollowUpPromptInput,
        settings: Settings,
    ) -> tuple[FollowUpOutput, FollowUpGuardResult]:
        """Generate a follow-up question via the dedicated pipeline.

        Pipeline: FollowUpPromptBuilder → LLM → STRICT Parser → FollowUpGuard.

        Raises:
            FollowUpParseError: on any structural or schema violation.
        """
        prompt = self._follow_up_prompt_builder.build(prompt_input)
        response = self._llm.invoke(prompt)
        content = response.content.strip()
        return self._follow_up_parser.parse(
            content,
            previous_answer=prompt_input.previous_answer,
            question_prompt=prompt_input.previous_question,
            question_area=prompt_input.question_area,
            settings=settings,
        )
