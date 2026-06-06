# services/question_intelligence/session_variety_memory.py

from domain.contracts.question.question import Question
from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.coverage.topic_extractor import TopicExtractor


class SessionVarietyMemoryHelper:

    def __init__(
        self,
        topic_extractor: TopicExtractor | None = None,
    ) -> None:

        self._topic_extractor = (
            topic_extractor
            if topic_extractor is not None
            else TopicExtractor()
        )

    def record_prompt(
        self,
        memory: InterviewRetrievalMemory,
        prompt: str,
    ) -> InterviewRetrievalMemory:

        normalized = prompt.strip()

        if not normalized or normalized in memory.session_selected_prompts:
            return memory

        topic = self._topic_extractor.extract(normalized)
        used_topics = list(memory.session_used_topics)

        if topic not in used_topics:
            used_topics.append(topic)

        return memory.model_copy(
            update={
                "session_selected_prompts": [
                    *memory.session_selected_prompts,
                    normalized,
                ],
                "session_used_topics": used_topics,
            },
        )

    def record_question(
        self,
        memory: InterviewRetrievalMemory,
        question: Question,
    ) -> InterviewRetrievalMemory:

        return self.record_prompt(
            memory=memory,
            prompt=question.prompt,
        )

    def record_bank_item(
        self,
        memory: InterviewRetrievalMemory,
        item: QuestionBankItem,
    ) -> InterviewRetrievalMemory:

        return self.record_prompt(
            memory=memory,
            prompt=item.text,
        )
