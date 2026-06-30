# domain/events/follow_up_triggered_event.py

from domain.events.interview_event import InterviewEvent


class FollowUpTriggeredEvent(InterviewEvent):
    """Emitted when a follow-up question is accepted by FollowUpGuard."""

    type: str = "follow_up_triggered"

    question_index: int
    question_area: str
    follow_up_count: int
    guard_score: float
    latency_ms: float
