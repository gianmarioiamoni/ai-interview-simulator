# services/question_intelligence/adaptive_interview_memory_bridge.py

from domain.contracts.question.question import Question
from domain.contracts.question.question_result import QuestionResult
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_intelligence.question_difficulty_mapper import (
    question_difficulty_to_corpus_int,
)
from services.question_intelligence.session_variety_memory import (
    SessionVarietyMemoryHelper,
)


class AdaptiveInterviewMemoryBridge:

    _WEAK_THRESHOLD = 0.6
    _STRONG_THRESHOLD = 0.85

    def __init__(
        self,
        memory_updater: InterviewMemoryUpdater | None = None,
    ) -> None:

        self._memory_updater = (
            memory_updater if memory_updater is not None else InterviewMemoryUpdater()
        )
        self._variety_memory = SessionVarietyMemoryHelper()

    def update_from_question_result(
        self,
        memory: InterviewRetrievalMemory,
        question: Question,
        result: QuestionResult | None,
    ) -> InterviewRetrievalMemory:

        evaluation_score = self._resolve_normalized_score(result)

        if evaluation_score is None:
            return self._record_selection(memory, question)

        return self._memory_updater.update_from_question_evaluation(
            memory=memory,
            question=question,
            evaluation_score=evaluation_score,
        )

    def _resolve_normalized_score(
        self,
        result: QuestionResult | None,
    ) -> float | None:

        if result is None:
            return None

        if result.evaluation is not None:
            return result.evaluation.score / 100.0

        execution = result.execution

        if execution is None:
            return None

        if execution.total_tests and execution.total_tests > 0:
            return execution.passed_tests / execution.total_tests

        return 1.0 if execution.success else 0.0

    def _record_selection(
        self,
        memory: InterviewRetrievalMemory,
        question: Question,
    ) -> InterviewRetrievalMemory:

        if question.id in memory.asked_question_ids:
            return memory

        difficulty_int = question_difficulty_to_corpus_int(question.difficulty)

        updated = memory.model_copy(
            update={
                "asked_question_ids": [*memory.asked_question_ids, question.id],
                "covered_domains": list(
                    set([*memory.covered_domains, question.area.value]),
                ),
                "difficulty_history": [*memory.difficulty_history, difficulty_int],
            },
        )

        return self._variety_memory.record_question(
            memory=updated,
            question=question,
        )
