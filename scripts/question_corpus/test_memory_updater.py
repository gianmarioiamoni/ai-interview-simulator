# scripts/question_corpus/test_memory_updater.py

from services.question_corpus.retrieval.chroma_retrieval_service import ChromaRetrievalService
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.retrieval.interview_memory_updater import InterviewMemoryUpdater


def main() -> None:

    retrieval = ChromaRetrievalService()

    results = retrieval.search(
        query="distributed systems",
        k=1,
    )

    candidate = results[0]

    memory = InterviewRetrievalMemory()

    updater = InterviewMemoryUpdater()

    updated = updater.update(
        memory=memory,
        candidate=candidate,
        evaluation_score=0.45,
    )

    print("\nUPDATED MEMORY\n")

    print(updated.model_dump())


if __name__ == "__main__":
    main()
