from domain.events.interview_event import InterviewEvent


class ExecutionCompletedEvent(InterviewEvent):

    type: str = "execution_completed"

    question_id: str
    success: bool
