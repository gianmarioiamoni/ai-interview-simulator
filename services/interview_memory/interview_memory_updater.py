# services/interview_memory/interview_memory_updater.py

from domain.contracts.interview.interview_memory_context import (
    InterviewMemoryContext,
)

from domain.contracts.question.question import Question


class InterviewMemoryUpdater:

    def update_after_question(
        self,
        memory: InterviewMemoryContext,
        question: Question,
    ) -> InterviewMemoryContext:

        covered_areas = list(memory.covered_areas)

        if question.area not in covered_areas:
            covered_areas.append(question.area)

        retrieval_history = list(memory.retrieval_history)

        retrieval_history.append(question.prompt)

        return InterviewMemoryContext(
            covered_areas=covered_areas,
            covered_concepts=memory.covered_concepts,
            weak_dimensions=memory.weak_dimensions,
            previous_failures=memory.previous_failures,
            retrieval_history=retrieval_history,
            follow_up_history=memory.follow_up_history,
        )
