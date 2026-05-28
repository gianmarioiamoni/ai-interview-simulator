# scripts/question_corpus/test_langchain_adapter.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.builders.retrieval_corpus_builder import RetrievalCorpusBuilder
from services.question_corpus.adapters.langchain_corpus_adapter import LangChainCorpusAdapter


def main() -> None:

    loader = FolderCorpusLoader()

    retrieval_builder = RetrievalCorpusBuilder()

    adapter = LangChainCorpusAdapter()

    corpus = loader.load(
        "datasets/curated/interview_seed",
    )

    retrieval_documents = retrieval_builder.build(
        corpus,
    )

    documents = adapter.adapt(
        retrieval_documents,
    )

    print("\nLANGCHAIN DOCUMENTS\n")

    print(f"Documents: {len(documents)}")

    first = documents[0]

    print("\nPAGE CONTENT\n")

    print(first.page_content)

    print("\nMETADATA\n")

    for key, value in first.metadata.items():

        print(f"{key}: {value}")


if __name__ == "__main__":

    main()
