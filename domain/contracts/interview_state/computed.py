# domain/contracts/interview_state/computed.py

from typing import Optional

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.interview_progress import InterviewProgress


class InterviewStateComputedMixin:

    @property
    def current_question(self) -> Optional[Question]:

        if not self.questions:
            return None

        if self.current_question_index >= len(self.questions):
            return None

        return self.questions[self.current_question_index]

    # ---------------------------------------------------------

    @property
    def last_answer(self) -> Optional[Answer]:

        if not self.answers:
            return None

        return self.answers[-1]

    # ---------------------------------------------------------

    @property
    def is_last_question(self) -> bool:

        if not self.questions:
            return False

        return self.current_question_index >= len(self.questions) - 1

    
    # ---------------------------------------------------------

    @property
    def is_completed(self) -> bool:
        return self.progress == InterviewProgress.COMPLETED