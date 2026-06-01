# scripts/question_corpus/test_chroma_search.py

from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime


def main() -> None:

    runtime = QuestionRetrievalRuntime()

    results = runtime.search(
        "distributed cache invalidation",
        k=3,
    )

    print("\nRETRIEVAL RESULTS\n")

    for index, result in enumerate(results):

        print(f"\nRESULT #{index + 1}\n")

        print(
            result.document.page_content,
        )

        print(f"\nFinal Score: {result.final_score}")

        print("\nMETADATA")

        for key, value in result.document.metadata.items():

            print(f"{key}: {value}")

        print("\nEMBEDDING")

        if result.embedding is None:

            print("None")

        else:

            print(
                len(
                    result.embedding,
                )
            )


if __name__ == "__main__":

    main()
