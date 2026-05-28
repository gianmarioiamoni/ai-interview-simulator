# services/question_corpus/builders/retrieval_document_builder.py

from domain.contracts.corpus import CuratedQuestion

from services.question_corpus.contracts.retrieval_document import RetrievalDocument


class RetrievalDocumentBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        question: CuratedQuestion,
    ) -> RetrievalDocument:

        retrieval_text = self._build_retrieval_text(
            question,
        )

        metadata = self._build_metadata(
            question,
        )

        return RetrievalDocument(
            document_id=question.id,
            text=retrieval_text,
            metadata=metadata,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _build_retrieval_text(
        self,
        question: CuratedQuestion,
    ) -> str:

        parts = [
            question.question,
            f"Role: {question.role.value}",
            f"Area: {question.area.value}",
            f"Seniority: {question.seniority.value}",
            f"Domains: {', '.join(question.domains)}",
            f"Topics: {', '.join(question.expected_topics)}",
        ]

        return "\n".join(parts)

    def _build_metadata(
        self,
        question: CuratedQuestion,
    ) -> dict[str, str | int | float | list[str]]:

        return {
            "role": question.role.value,
            "area": question.area.value,
            "seniority": question.seniority.value,
            "difficulty": question.difficulty,
            "domains": question.domains,
            "tags": question.tags,
            "quality_score": question.quality_score,
            "source": question.source,
        }
