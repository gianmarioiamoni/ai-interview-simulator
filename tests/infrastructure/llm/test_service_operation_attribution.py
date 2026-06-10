# tests/infrastructure/llm/test_service_operation_attribution.py

import json
from typing import Type, TypeVar
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from pydantic import BaseModel

from infrastructure.llm.metrics.interview_metrics_collector import (
    InterviewMetricsCollector,
)
from infrastructure.llm.metrics.llm_operation_names import (
    ANSWER_IMPROVEMENT,
    NARRATIVE_GENERATION,
    QUESTION_GENERATION,
)
from infrastructure.llm.observability.observing_llm_adapter import ObservingLLMAdapter
from services.answer_improvement.answer_improver import AnswerImprover
from services.narrative_service import NarrativeService
from services.question_intelligence.question_generator import QuestionGenerator

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

T = TypeVar("T", bound=BaseModel)


class _StubResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _StubLLMPort:
    def __init__(self, raw_llm: MagicMock) -> None:
        self._llm = raw_llm

    def invoke(self, prompt: str, system_prompt: str | None = None) -> _StubResponse:
        raw = self._llm.invoke([{"role": "user", "content": prompt}])
        return _StubResponse(content=getattr(raw, "content", ""))

    def invoke_json(self, prompt: str, schema: Type[T]) -> T:
        raw = self._llm.invoke([{"role": "user", "content": prompt}])
        return schema.model_validate(json.loads(getattr(raw, "content", "")))


def _build_observing_adapter(
    collector: InterviewMetricsCollector,
    content: str,
) -> ObservingLLMAdapter:
    raw_llm = MagicMock()
    raw_llm.model_name = "gpt-4o-mini"
    raw_llm.invoke.return_value = AIMessage(
        content=content,
        usage_metadata={
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        },
        response_metadata={"model_name": "gpt-4o-mini", "finish_reason": "stop"},
    )
    return ObservingLLMAdapter(_StubLLMPort(raw_llm), collector)


def test_question_generator_attributes_question_generation() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    payload = json.dumps([{"text": "What is CAP?", "difficulty": 3}])
    llm = _build_observing_adapter(collector, payload)
    generator = QuestionGenerator(llm)

    questions = generator.generate(
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        n=1,
    )

    assert len(questions) == 1
    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == QUESTION_GENERATION


def test_answer_improver_attributes_answer_improvement() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    llm = _build_observing_adapter(collector, "Improved answer")
    improver = AnswerImprover(llm)

    result = improver.improve(
        question="Explain caching",
        user_answer="It stores data",
        feedback="Add more detail",
    )

    assert result == "Improved answer"
    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == ANSWER_IMPROVEMENT


def test_narrative_service_attributes_narrative_generation() -> None:
    collector = InterviewMetricsCollector()
    collector.start_session()

    llm = _build_observing_adapter(collector, "Executive summary text")
    service = NarrativeService(llm)

    summary = service.generate_executive_summary(
        decision="hire",
        overall_score=82.0,
        strongest="System Design",
        weakest="Communication",
        percentile=75.0,
        strongest_score=90.0,
        weakest_score=70.0,
    )

    assert summary == "Executive summary text"
    metrics = collector.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].operation == NARRATIVE_GENERATION
