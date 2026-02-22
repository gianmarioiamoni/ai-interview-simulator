# Retriever abstraction

from typing import List
from langchain.schema import Document

class Retriever:
    def retrieve(self, query: str) -> List[Document]:
        # Placeholder: integrazione LangChain
        return []
