# scripts/question_corpus/test_retrieval_builder.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.builders.retrieval_corpus_builder import RetrievalCorpusBuilder


def main() -> None:

    loader = FolderCorpusLoader()

    builder = RetrievalCorpusBuilder()

    corpus = loader.load(
        "datasets/curated/interview_seed",
    )

    documents = builder.build(
        corpus,
    )

    print("\nRETRIEVAL DOCUMENTS\n")

    print(f"Documents: {len(documents)}")

    first = documents[0]

    print("\nDOCUMENT ID")

    print(first.document_id)

    print("\nTEXT")

    print(first.text)

    print("\nMETADATA")

    for key, value in first.metadata.items():

        print(f"{key}: {value}")


if __name__ == "__main__":

    main()
