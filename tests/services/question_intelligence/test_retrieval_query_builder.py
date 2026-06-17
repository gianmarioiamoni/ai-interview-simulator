# tests/services/question_intelligence/test_retrieval_query_builder.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.sql_domain import SqlDomain
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.retrieval_query_builder import (
    RetrievalQueryBuilder,
)


def test_retrieval_query_builder_includes_theme_anchor() -> None:

    query = RetrievalQueryBuilder().build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        area=InterviewArea.TECH_DATABASE,
        theme_anchor="distributed_systems",
    )

    assert "distributed systems" in query.lower()


def test_retrieval_query_builder_varies_by_role_and_level() -> None:

    builder = RetrievalQueryBuilder()

    junior_backend = builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.JUNIOR,
        area=InterviewArea.TECH_DATABASE,
    )
    senior_data = builder.build(
        role=RoleType.DATA_ENGINEER,
        level=SeniorityLevel.SENIOR,
        area=InterviewArea.TECH_DATABASE,
    )

    assert junior_backend != senior_data
    assert "entry-level" in junior_backend.lower()
    assert "advanced database design" in senior_data.lower()


def test_retrieval_query_builder_rotates_with_memory() -> None:

    builder = RetrievalQueryBuilder()
    base_kwargs = {
        "role": RoleType.BACKEND_ENGINEER,
        "level": SeniorityLevel.MID,
        "area": InterviewArea.TECH_DATABASE,
    }

    first = builder.build(**base_kwargs, memory=InterviewRetrievalMemory())
    second = builder.build(
        **base_kwargs,
        memory=InterviewRetrievalMemory(asked_question_ids=["q1", "q2"]),
    )

    assert first != second


def test_retrieval_query_builder_includes_adaptive_domains() -> None:

    memory = InterviewRetrievalMemory(
        weak_domains=[SqlDomain.INDEXING, SqlDomain.TRANSACTION],
        strong_domains=[SqlDomain.JOIN],
    )
    query = RetrievalQueryBuilder().build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        area=InterviewArea.TECH_DATABASE,
        memory=memory,
    )

    assert "indexing" in query.lower()
    assert "transaction" in query.lower()
    assert "not join" in query.lower()
