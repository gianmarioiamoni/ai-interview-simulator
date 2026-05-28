# services/question_corpus/cli/test_seed_loader.py

from services.question_corpus.loaders.json_corpus_loader import JsonCorpusLoader


def main() -> None:

    loader = JsonCorpusLoader()

    corpus = loader.load(
        path="datasets/curated/interview_seed/backend/backend_seed.json",
    )

    print("\nCORPUS LOADED\n")

    print(f"Questions: {len(corpus.questions)}")

    for question in corpus.questions:

        print("\n-----------------------------------")
        print(f"ID: {question.id}")
        print(f"Question: {question.question}")
        print(f"Role: {question.role}")
        print(f"Area: {question.area}")
        print(f"Difficulty: {question.difficulty}")
        print(f"Domains: {question.domains}")


if __name__ == "__main__":

    main()
