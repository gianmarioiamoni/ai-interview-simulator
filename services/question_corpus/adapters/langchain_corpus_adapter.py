# services/question_corpus/adapters/langchain_corpus_adapter.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_document import RetrievalDocument
from services.question_corpus.adapters.langchain_document_adapter import LangChainDocumentAdapter



class LangChainCorpusAdapter:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._adapter = LangChainDocumentAdapter()

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        documents: list[RetrievalDocument],
    ) -> list[Document]:

        return [self._adapter.adapt(document) for document in documents]
