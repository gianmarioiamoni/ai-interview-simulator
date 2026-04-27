# app/ports/llm_port.py

from typing import Protocol, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMResponse(Protocol):
    content: str


class LLMPort(Protocol):

    def invoke(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse: ...

    def invoke_json(
        self,
        prompt: str,
        schema: Type[T],
    ) -> T: ...
