# domain/events/follow_up_skipped_event.py

from domain.events.interview_event import InterviewEvent


class FollowUpSkippedEvent(InterviewEvent):
    """Emitted when a follow-up slot exists but the guard rejects the output
    or the parser fails, or supports_follow_up=False."""

    type: str = "follow_up_skipped"

    question_index: int
    question_area: str | None
    reason: str                     # "guard_rejected" | "parse_error" | "flag_disabled" | "no_context"
    failed_rules: tuple[str, ...]
    latency_ms: float
