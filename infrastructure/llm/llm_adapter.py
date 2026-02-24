# infrastructure/llm/llm_adapter.py

from infrastructure.llm.llm_factory import get_llm
from app.ports.llm_port import LLMPort


class DefaultLLMAdapter(LLMPort):

    def __init__(self):
        self._llm = get_llm()

    def invoke(self, prompt: str):
        return self._llm.invoke(prompt)
