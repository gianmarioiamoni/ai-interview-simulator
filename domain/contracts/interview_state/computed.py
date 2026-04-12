# domain/contracts/interview_state/computed.py

from typing import Optional

from domain.contracts.question.question import Question
from domain.contracts.interview.answer import Answer


class InterviewStateComputedMixin:

    @property
    def current_question(self) -> Optional[Question]:

        if not self.questions:
            return None

        if self.current_question_index < 0:
            return None

        if self.current_question_index >= len(self.questions):
            return None

        
        return self.questions[self.current_question_index]

    # ---------------------------------------------------------

    def get_attempt_for_question(self, question_id: str) -> int:
        return sum(1 for a in self.answers if a.question_id == question_id)

    # ---------------------------------------------------------

    def add_answer(self, answer: Answer):
        return self.model_copy(update={"answers": self.answers + [answer]})


    # ---------------------------------------------------------
    # ANSWERS BY QUESTION
    # ---------------------------------------------------------

    def get_answers_for_question(self, question_id: str) -> list[Answer]:
        return [a for a in self.answers if a.question_id == question_id]

    # ---------------------------------------------------------

    def get_latest_answer_for_question(self, question_id: str) -> Optional[Answer]:

        answers = self.get_answers_for_question(question_id)

        if not answers:
            return None

        return answers[-1]
