# RAG orchestration layer

from domain.retrieval.retriever import Retriever
from domain.generation.answer_generator import AnswerGenerator

class RAGPipeline:
    def __init__(self) -> None:
        self._retriever = Retriever()
        self._generator = AnswerGenerator()

    def run(self, query: str) -> str:
        documents = self._retriever.retrieve(query)
        return self._generator.generate(query, documents)
