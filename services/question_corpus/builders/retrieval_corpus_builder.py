# services/question_corpus/builders/retrieval_corpus_builder.py

from domain.contracts.corpus import QuestionCorpus

from services.question_corpus.contracts.retrieval_document import RetrievalDocument
from services.question_corpus.builders.retrieval_document_builder import RetrievalDocumentBuilder


class RetrievalCorpusBuilder:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._document_builder = RetrievalDocumentBuilder()

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        corpus: QuestionCorpus,
    ) -> list[RetrievalDocument]:

        return [self._document_builder.build(question) for question in corpus.questions]
