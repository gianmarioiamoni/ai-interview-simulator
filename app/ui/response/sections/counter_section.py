# app/ui/response/sections/counter_section.py

from domain.contracts.interview_state import InterviewState


class CounterSection:

    @staticmethod
    def build(state: InterviewState, question, attempts: int, max_attempts: int) -> str:

        if state.adaptive_interview_enabled and state.planned_areas:
            total = len(state.planned_areas)
        else:
            total = len(state.questions)

        index = state.current_question_index + 1

        return (
            f"Question {index} / {total}\n\n" f"Attempt {attempts} / {max_attempts}"
        )
