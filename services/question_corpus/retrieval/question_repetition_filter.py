# services/question_corpus/retrieval/question_repetition_filter.py

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate


class QuestionRepetitionFilter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply(
        self,
        candidates: list[RetrievalCandidate],
        memory: InterviewRetrievalMemory,
    ) -> list[RetrievalCandidate]:

        asked_ids = set(
            memory.asked_question_ids,
        )

        filtered: list[RetrievalCandidate] = []

        for candidate in candidates:

            document_id = candidate.document.metadata.get(
                "document_id",
                "",
            )

            if document_id in asked_ids:
                continue

            filtered.append(
                candidate,
            )

        return filtered
