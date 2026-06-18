# services/question_corpus/builders/retrieval_document_builder.py

from domain.contracts.corpus import CuratedQuestion

from infrastructure.embeddings.embedding_factory import get_embedding_model

from services.question_corpus.contracts.retrieval_document import RetrievalDocument
from services.question_corpus.repositories.retrieval_embedding_repository import RetrievalEmbeddingRepository


class RetrievalDocumentBuilder:

    def __init__(
        self,
        skip_embedding: bool = False,
    ) -> None:

        self._skip_embedding = skip_embedding

        self._embedding_model = (
            None if skip_embedding else get_embedding_model()
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        question: CuratedQuestion,
    ) -> RetrievalDocument:

        display_text = self._build_display_text(
            question,
        )

        embedding_text = self._build_embedding_text(
            question,
        )

        if self._skip_embedding:

            embedding: list[float] = []

        else:

            embedding = self._embedding_model.embed_query(
                embedding_text,
            )

            RetrievalEmbeddingRepository.store(
                document_id=question.id,
                embedding=embedding,
            )

        metadata = self._build_metadata(
            question,
        )

        return RetrievalDocument(
            document_id=question.id,
            text=display_text,
            metadata=metadata,
            embedding=embedding,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _build_display_text(
        self,
        question: CuratedQuestion,
    ) -> str:

        return question.question.strip()

    def _build_embedding_text(
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
            "expected_topics": question.expected_topics,
            "tags": question.tags,
            "quality_score": question.quality_score,
            "source": question.source,
        }
