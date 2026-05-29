# scripts/question_corpus/test_chroma_search.py

from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService


def main() -> None:

    retrieval = ChromaRetrievalService()

    results = retrieval.search(
        "distributed cache invalidation",
        k=3,
    )

    print("\nRETRIEVAL RESULTS\n")

    for index, result in enumerate(results):

        print(f"\nRESULT #{index + 1}\n")

        print(result.page_content)

        print("\nMETADATA")

        for key, value in result.metadata.items():

            print(f"{key}: {value}")

        print("\nEMBEDDING")
        print(
            len(
                results[0].embedding,
            )
        )
if __name__ == "__main__":

    main()
