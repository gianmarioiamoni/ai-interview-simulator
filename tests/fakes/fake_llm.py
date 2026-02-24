# tests/fakes/fake_llm.py

from app.ports.llm_port import LLMPort


class FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM(LLMPort):

    def __init__(self, scripted_responses: list[str]):
        self._responses = scripted_responses
        self._index = 0

    def invoke(self, prompt: str) -> FakeLLMResponse:
        if self._index >= len(self._responses):
            raise RuntimeError("No more scripted LLM responses.")

        response = self._responses[self._index]
        self._index += 1

        return FakeLLMResponse(response)
