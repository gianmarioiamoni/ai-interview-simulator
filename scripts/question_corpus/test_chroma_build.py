# scripts/question_corpus/test_chroma_build.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.builders.retrieval_corpus_builder import RetrievalCorpusBuilder
from services.question_corpus.adapters.langchain_corpus_adapter import LangChainCorpusAdapter
from services.question_corpus.vectorstores.chroma_corpus_builder import ChromaCorpusBuilder


def main() -> None:

    loader = FolderCorpusLoader()

    retrieval_builder = RetrievalCorpusBuilder()

    adapter = LangChainCorpusAdapter()

    chroma_builder = ChromaCorpusBuilder()

    corpus = loader.load(
        "datasets/curated/interview_seed",
    )

    retrieval_documents = retrieval_builder.build(
        corpus,
    )

    langchain_documents = adapter.adapt(
        retrieval_documents,
    )

    chroma_builder.build(
        langchain_documents,
    )
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    db = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory="storage/chroma/interview_corpus",
    )

    print(
        db._collection.count(),
    )

    print("\nCHROMA BUILD COMPLETED\n")


if __name__ == "__main__":

    main()
