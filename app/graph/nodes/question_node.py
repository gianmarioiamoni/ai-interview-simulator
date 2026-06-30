# app/graph/nodes/question_node.py

import logging
import time
from dataclasses import dataclass

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType
from domain.events.follow_up_triggered_event import FollowUpTriggeredEvent
from domain.events.follow_up_skipped_event import FollowUpSkippedEvent

from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.humanizer_service import HumanizerService
from services.humanizer.follow_up.follow_up_prompt_input import FollowUpPromptInput
from services.humanizer.follow_up.follow_up_parse_error import FollowUpParseError
from services.interview_memory.interview_memory_updater import InterviewMemoryUpdater
from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


def _build_display_prompt(question) -> str:
    return question.prompt


def _is_follow_up_eligible(state: InterviewState, question) -> bool:
    return (
        state.current_question_index in state.follow_up_eligible_indices
        and question.supports_follow_up
        and state.follow_up_count < settings.max_follow_ups_per_interview
    )


def _build_follow_up_prompt_input(state: InterviewState) -> FollowUpPromptInput | None:
    ctx = state.last_question_context
    if ctx is None or not ctx.answer_content:
        return None

    profile = state.context_profile
    feedback_text = ""
    if state.last_feedback_bundle is not None:
        feedback_text = str(state.last_feedback_bundle.overall_quality)

    return FollowUpPromptInput(
        question_area=ctx.question_area or "",
        previous_question=ctx.question_prompt,
        previous_answer=ctx.answer_content[:settings.follow_up_max_input_chars],
        previous_feedback=feedback_text,
        candidate_level=state.seniority_level,
        role=str(state.role.type.value) if state.role else "",
        seniority=state.seniority_level,
        job_description=profile.job_description or "",
        company_description=profile.company_description or "",
        business_context=str(profile.business_context.value) if profile.business_context else "",
        follow_up_type="deep_dive",
    )


@dataclass
class _FollowUpAttemptResult:
    """Internal carrier: follow-up text (if accepted) + event to record."""
    accepted: bool
    follow_up_text: str | None
    event: FollowUpTriggeredEvent | FollowUpSkippedEvent


def _attempt_follow_up(
    state: InterviewState,
    question,
    humanizer_service: HumanizerService,
) -> _FollowUpAttemptResult:
    """Run the follow-up pipeline and return an attempt result. Never raises."""

    t0 = time.perf_counter()

    prompt_input = _build_follow_up_prompt_input(state)
    if prompt_input is None:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return _FollowUpAttemptResult(
            accepted=False,
            follow_up_text=None,
            event=FollowUpSkippedEvent(
                question_index=state.current_question_index,
                question_area=None,
                reason="no_context",
                failed_rules=(),
                latency_ms=latency_ms,
            ),
        )

    try:
        follow_up_output, guard_result = humanizer_service.generate_follow_up(
            prompt_input=prompt_input,
            settings=settings,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        if guard_result.accepted:
            return _FollowUpAttemptResult(
                accepted=True,
                follow_up_text=follow_up_output.follow_up_question,
                event=FollowUpTriggeredEvent(
                    question_index=state.current_question_index,
                    question_area=prompt_input.question_area,
                    follow_up_count=state.follow_up_count + 1,
                    guard_score=guard_result.score,
                    latency_ms=latency_ms,
                ),
            )
        else:
            return _FollowUpAttemptResult(
                accepted=False,
                follow_up_text=None,
                event=FollowUpSkippedEvent(
                    question_index=state.current_question_index,
                    question_area=prompt_input.question_area,
                    reason="guard_rejected",
                    failed_rules=tuple(guard_result.failed_rules),
                    latency_ms=latency_ms,
                ),
            )

    except FollowUpParseError as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return _FollowUpAttemptResult(
            accepted=False,
            follow_up_text=None,
            event=FollowUpSkippedEvent(
                question_index=state.current_question_index,
                question_area=prompt_input.question_area,
                reason="parse_error",
                failed_rules=(),
                latency_ms=latency_ms,
            ),
        )

    except Exception:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.warning("follow_up_generation_failed", exc_info=True)
        return _FollowUpAttemptResult(
            accepted=False,
            follow_up_text=None,
            event=FollowUpSkippedEvent(
                question_index=state.current_question_index,
                question_area=getattr(prompt_input, "question_area", None),
                reason="parse_error",
                failed_rules=(),
                latency_ms=latency_ms,
            ),
        )


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

            raw_text = _build_display_prompt(question)
            new_history = state.chat_history + [raw_text]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                    "question_display_text": raw_text,
                }
            )

        # ---------------------------------------------------------
        # Non written questions
        # ---------------------------------------------------------

        if question.type != QuestionType.WRITTEN:

            raw_text = _build_display_prompt(question)
            new_history = state.chat_history + [raw_text]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                    "question_display_text": raw_text,
                }
            )

        # ---------------------------------------------------------
        # Follow-up pipeline (V1.1)
        # ---------------------------------------------------------

        extra_events: list = []

        if (
            settings.humanizer_follow_up_enabled
            and _is_follow_up_eligible(state, question)
        ):
            attempt = _attempt_follow_up(state, question, humanizer_service)
            extra_events.append(attempt.event)

            if settings.follow_up_logging_enabled:
                _log_attempt(attempt)

            if attempt.accepted:
                updated_memory = memory_updater.update_after_question(
                    memory=state.memory_context,
                    question=question,
                )
                return state.model_copy(
                    update={
                        "chat_history": state.chat_history + [attempt.follow_up_text],
                        "question_display_text": attempt.follow_up_text,
                        "follow_up_count": state.follow_up_count + 1,
                        "last_humanizer_follow_up": True,
                        "memory_context": updated_memory,
                        "events": list(state.events) + extra_events,
                    }
                )
            # Guard rejected or parse error → fall through to V1.0

        # ---------------------------------------------------------
        # Standard V1.0 humanizer path
        # ---------------------------------------------------------

        last_answer = None
        last_score = None

        if state.answers:
            last_answer = state.answers[-1].content

        if state.last_feedback_bundle:
            last_score = state.last_feedback_bundle.overall_quality.rank()
        elif state.last_question_context is not None:
            last_score = state.last_question_context.quality_rank

        ctx = state.last_question_context
        previous_question = ctx.question_prompt if ctx is not None else None
        previous_answer = ctx.answer_content if ctx is not None else None
        previous_score = float(ctx.quality_rank) if ctx is not None and ctx.quality_rank is not None else None
        previous_area = ctx.question_area if ctx is not None else None

        input_data = HumanizerInput(
            current_question=question,
            language=state.language,
            chat_history=state.chat_history,
            last_answer=last_answer,
            last_answer_score=last_score,
            follow_up_count=state.follow_up_count,
            last_turn_was_follow_up=(state.last_humanizer_follow_up),
            previous_question=previous_question,
            previous_answer=previous_answer,
            previous_score=previous_score,
            previous_area=previous_area,
        )

        try:
            policy_decision, output = humanizer_service.humanize(
                input_data=input_data,
            )
            humanized_text = output.message
        except Exception:
            logger.warning("humanizer_failed", exc_info=True)
            policy_decision = None
            humanized_text = question.prompt

        is_follow_up = policy_decision == HumanizerDecision.FOLLOW_UP

        follow_up_count = (
            state.follow_up_count + 1 if is_follow_up else state.follow_up_count
        )

        new_history = state.chat_history + [humanized_text]

        updated_memory = memory_updater.update_after_question(
            memory=state.memory_context,
            question=question,
        )

        return state.model_copy(
            update={
                "chat_history": new_history,
                "question_display_text": humanized_text,
                "follow_up_count": follow_up_count,
                "last_humanizer_follow_up": is_follow_up,
                "memory_context": updated_memory,
                "events": list(state.events) + extra_events,
            }
        )

    return question_node


def _log_attempt(attempt: _FollowUpAttemptResult) -> None:
    if attempt.accepted:
        logger.info(
            "follow_up_triggered",
            extra={
                "question_index": attempt.event.question_index,
                "question_area": attempt.event.question_area,
                "guard_score": attempt.event.guard_score,
                "latency_ms": attempt.event.latency_ms,
            },
        )
    else:
        logger.info(
            "follow_up_skipped",
            extra={
                "question_index": attempt.event.question_index,
                "reason": attempt.event.reason,
                "failed_rules": list(attempt.event.failed_rules),
                "latency_ms": attempt.event.latency_ms,
            },
        )
