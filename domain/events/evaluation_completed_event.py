from domain.events.interview_event import InterviewEvent


class EvaluationCompletedEvent(InterviewEvent):

    type: str = "evaluation_completed"

    question_id: str
    score: float
