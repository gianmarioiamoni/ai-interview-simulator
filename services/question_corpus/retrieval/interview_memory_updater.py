# services/question_corpus/retrieval/interview_memory_updater.py

from domain.contracts.question.question import Question
from domain.contracts.question.question_bank_item import QuestionBankItem

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.question_difficulty_mapper import (
    question_difficulty_to_corpus_int,
)
from services.question_intelligence.session_variety_memory import (
    SessionVarietyMemoryHelper,
)


class InterviewMemoryUpdater:

    def __init__(
        self,
        variety_memory_helper: SessionVarietyMemoryHelper | None = None,
    ) -> None:

        self._variety_memory = (
            variety_memory_helper
            if variety_memory_helper is not None
            else SessionVarietyMemoryHelper()
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def record_bank_item_selection(
        self,
        memory: InterviewRetrievalMemory,
        item: QuestionBankItem,
    ) -> InterviewRetrievalMemory:

        question_id = item.id.strip()

        if not question_id or question_id in memory.asked_question_ids:
            return memory

        domains = [item.area.value]

        updated = InterviewRetrievalMemory(
            asked_question_ids=[
                *memory.asked_question_ids,
                question_id,
            ],
            covered_domains=list(
                set(
                    memory.covered_domains + domains,
                ),
            ),
            weak_domains=list(
                memory.weak_domains,
            ),
            strong_domains=list(
                memory.strong_domains,
            ),
            difficulty_history=[
                *memory.difficulty_history,
                item.difficulty,
            ],
            average_score=memory.average_score,
            question_count=memory.question_count,
            session_selected_prompts=list(memory.session_selected_prompts),
            session_used_topics=list(memory.session_used_topics),
        )

        return self._variety_memory.record_bank_item(
            memory=updated,
            item=item,
        )

    def update_from_question_evaluation(
        self,
        memory: InterviewRetrievalMemory,
        question: Question,
        evaluation_score: float,
    ) -> InterviewRetrievalMemory:

        question_id = question.id.strip()

        domains = [question.area.value]
        weak_domains = list(memory.weak_domains)
        strong_domains = list(memory.strong_domains)

        if evaluation_score < 0.6:
            for domain in domains:
                if domain not in weak_domains:
                    weak_domains.append(domain)

        elif evaluation_score >= 0.85:
            for domain in domains:
                if domain not in strong_domains:
                    strong_domains.append(domain)

        total_score = memory.average_score * memory.question_count
        total_score += evaluation_score
        new_count = memory.question_count + 1
        new_average = total_score / new_count if new_count else evaluation_score

        asked_question_ids = list(memory.asked_question_ids)

        if question_id and question_id not in asked_question_ids:
            asked_question_ids.append(question_id)

        difficulty_int = question_difficulty_to_corpus_int(question.difficulty)

        updated = InterviewRetrievalMemory(
            asked_question_ids=asked_question_ids,
            covered_domains=list(set(memory.covered_domains + domains)),
            weak_domains=weak_domains,
            strong_domains=strong_domains,
            difficulty_history=[*memory.difficulty_history, difficulty_int],
            average_score=round(new_average, 3),
            question_count=new_count,
            session_selected_prompts=list(memory.session_selected_prompts),
            session_used_topics=list(memory.session_used_topics),
        )

        return self._variety_memory.record_question(
            memory=updated,
            question=question,
        )

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
            session_selected_prompts=list(memory.session_selected_prompts),
            session_used_topics=list(memory.session_used_topics),
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
