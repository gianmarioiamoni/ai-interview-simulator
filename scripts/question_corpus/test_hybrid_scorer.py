# scripts/question_corpus/test_hybrid_scorer.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_result import (
    RetrievalResult,
)
from services.question_corpus.retrieval.hybrid_retrieval_scorer import (
    HybridRetrievalScorer,
)


def main() -> None:

    scorer = HybridRetrievalScorer()

    result = RetrievalResult(
        document=Document(
            page_content="How would you design a distributed cache?",
            metadata={
                "document_id": "test_001",
            },
        ),
        distance=0.25,
        semantic_score=0.75,
        quality_score=0.95,
        embedding=[
            0.1,
            0.2,
            0.3,
        ],
    )

    candidate = scorer.score(
        result,
    )

    print("\nRETRIEVAL CANDIDATE\n")

    print(f"Document ID: " f"{candidate.document.metadata['document_id']}")

    print(f"Semantic Score: " f"{candidate.semantic_score}")

    print(f"Quality Score: " f"{candidate.quality_score}")

    print(f"Final Score: " f"{candidate.final_score}")

    print(f"Embedding Length: " f"{len(candidate.embedding)}")


if __name__ == "__main__":

    main()
