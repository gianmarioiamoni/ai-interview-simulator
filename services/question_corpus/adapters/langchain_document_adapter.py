# services/question_corpus/adapters/langchain_document_adapter.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_document import RetrievalDocument
from services.question_corpus.utils.domain_parser import serialize_domains


class LangChainDocumentAdapter:

    def adapt(
        self,
        retrieval_document: RetrievalDocument,
    ) -> Document:

        metadata = dict(
            retrieval_document.metadata,
        )

        metadata["domains"] = serialize_domains(metadata.get("domains"))

        metadata["tags"] = serialize_domains(metadata.get("tags"))

        metadata["document_id"] = retrieval_document.document_id

        return Document(
            page_content=retrieval_document.text,
            metadata=metadata,
        )
