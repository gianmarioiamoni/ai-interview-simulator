# scripts/question_corpus/test_interview_memory.py

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


def main() -> None:

    memory = InterviewRetrievalMemory()

    print("\nINTERVIEW MEMORY\n")

    print(memory.model_dump())


if __name__ == "__main__":
    main()
