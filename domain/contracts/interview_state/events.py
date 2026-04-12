# domain/contracts/interview_state/events.py

from domain.events.answer_submitted_event import AnswerSubmittedEvent


class InterviewStateEventsMixin:

    def apply_event(self, event):

        new_state = self.model_copy(deep=True)

        new_state.events.append(event)

        if isinstance(event, AnswerSubmittedEvent):

            from domain.contracts.interview.answer import Answer

            new_state.answers.append(
                Answer(
                    question_id=event.question_id,
                    content=event.content,
                    attempt=1,
                )
            )

        return new_state
