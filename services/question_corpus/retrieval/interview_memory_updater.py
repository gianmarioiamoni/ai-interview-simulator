# services/question_corpus/retrieval/interview_memory_updater.py

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate


class InterviewMemoryUpdater:

    # =====================================================
    # PUBLIC
    # =====================================================

    def update(
        self,
        memory: InterviewRetrievalMemory,
        candidate: RetrievalCandidate,
        evaluation_score: float,
    ) -> InterviewRetrievalMemory:

        metadata = candidate.document.metadata

        question_id = metadata.get(
            "document_id",
            "",
        )

        domains = self._extract_domains(
            candidate,
        )

        weak_domains = list(
            memory.weak_domains,
        )

        strong_domains = list(
            memory.strong_domains,
        )

        # -------------------------------------------------
        # PERFORMANCE ANALYSIS
        # -------------------------------------------------

        if evaluation_score < 0.6:

            for domain in domains:

                if domain not in weak_domains:
                    weak_domains.append(domain)

        elif evaluation_score >= 0.85:

            for domain in domains:

                if domain not in strong_domains:
                    strong_domains.append(domain)

        # -------------------------------------------------
        # AVERAGE SCORE
        # -------------------------------------------------

        total_score = memory.average_score * memory.question_count

        total_score += evaluation_score

        new_count = memory.question_count + 1

        new_average = total_score / new_count

        return InterviewRetrievalMemory(
            asked_question_ids=[
                *memory.asked_question_ids,
                question_id,
            ],
            covered_domains=list(set(memory.covered_domains + domains)),
            weak_domains=weak_domains,
            strong_domains=strong_domains,
            difficulty_history=[
                *memory.difficulty_history,
                int(metadata.get("difficulty", 0)),
            ],
            average_score=round(
                new_average,
                3,
            ),
            question_count=new_count,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _extract_domains(
        self,
        candidate: RetrievalCandidate,
    ) -> list[str]:

        domains = candidate.document.metadata.get(
            "domains",
            "",
        )

        if not domains:
            return []

        return [d.strip() for d in domains.split(",")]
