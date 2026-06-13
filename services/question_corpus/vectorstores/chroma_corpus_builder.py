# services/question_corpus/vectorstores/chroma_corpus_builder.py

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from infrastructure.config.settings import settings
from services.question_corpus.constants.vector_store_constants import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIRECTORY,
)


class ChromaCorpusBuilder:

    def __init__(
        self,
    ) -> None:

        self._embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)

    def build(
        self,
        documents: list[Document],
    ) -> Chroma:

        try:

            existing = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=self._embeddings,
                persist_directory=CHROMA_PERSIST_DIRECTORY,
            )

            existing.delete_collection()

        except Exception:
            pass

        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self._embeddings,
            collection_name=CHROMA_COLLECTION_NAME,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
        )

        return vectorstore
