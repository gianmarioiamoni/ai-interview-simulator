# services/question_corpus/adapters/langchain_document_adapter.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_document import (
    RetrievalDocument,
)


class LangChainDocumentAdapter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        retrieval_document: RetrievalDocument,
    ) -> Document:

        metadata = dict(
            retrieval_document.metadata,
        )

        # -------------------------------------------------
        # CHROMA SAFE METADATA
        # -------------------------------------------------

        metadata["domains"] = ",".join(
            metadata.get("domains", []),
        )

        metadata["tags"] = ",".join(
            metadata.get("tags", []),
        )

        metadata["document_id"] = retrieval_document.document_id

        return Document(
            page_content=retrieval_document.text,
            metadata=metadata,
        )
