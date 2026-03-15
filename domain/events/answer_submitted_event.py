from domain.events.interview_event import InterviewEvent


class AnswerSubmittedEvent(InterviewEvent):

    type: str = "answer_submitted"

    question_id: str
    content: str
