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
        skip_embedding: bool = False,
    ) -> None:

        self._document_builder = RetrievalDocumentBuilder(
            skip_embedding=skip_embedding,
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        corpus: QuestionCorpus,
    ) -> list[RetrievalDocument]:

        return [self._document_builder.build(question) for question in corpus.questions]
