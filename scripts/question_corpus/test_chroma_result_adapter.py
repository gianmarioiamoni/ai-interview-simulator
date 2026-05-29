# scripts/question_corpus/test_chroma_result_adapter.py

from services.question_corpus.adapters.chroma_result_adapter import (
    ChromaResultAdapter,
)


def main() -> None:

    raw_results = {
        "documents": [
            [
                "Question A",
            ]
        ],
        "metadatas": [
            [
                {
                    "quality_score": 0.95,
                    "document_id": "q1",
                }
            ]
        ],
        "distances": [
            [
                0.25,
            ]
        ],
        "embeddings": [
            [
                [
                    0.1,
                    0.2,
                    0.3,
                ]
            ]
        ],
    }

    adapter = ChromaResultAdapter()

    results = adapter.adapt(
        raw_results,
    )

    print(
        results[0],
    )


if __name__ == "__main__":

    main()
