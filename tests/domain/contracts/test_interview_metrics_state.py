# tests/domain/contracts/test_interview_metrics_state.py

from domain.contracts.interview.interview_metrics import InterviewMetrics, OperationMetrics
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import Role, RoleType


def test_interview_state_defaults_interview_metrics_to_none() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="AuditCo",
        language="en",
    )

    assert state.interview_metrics is None


def test_interview_state_serializes_interview_metrics() -> None:
    metrics = InterviewMetrics(
        total_calls=2,
        total_input_tokens=20,
        total_output_tokens=10,
        total_tokens=30,
        total_retries=1,
        avg_latency_ms=150.0,
        operations=[
            OperationMetrics(
                operation="written_evaluation",
                calls=2,
                input_tokens=20,
                output_tokens=10,
                total_tokens=30,
                avg_latency_ms=150.0,
            )
        ],
    )

    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="AuditCo",
        language="en",
        interview_metrics=metrics,
    )

    restored = InterviewState.model_validate(state.model_dump())

    assert restored.interview_metrics is not None
    assert restored.interview_metrics.total_tokens == 30
    assert restored.interview_metrics.operations[0].operation == "written_evaluation"


def test_interview_state_merge_update_interview_metrics() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="AuditCo",
        language="en",
    )

    metrics = InterviewMetrics(
        total_calls=1,
        total_input_tokens=10,
        total_output_tokens=5,
        total_tokens=15,
        total_retries=0,
        avg_latency_ms=100.0,
        operations=[],
    )

    updated = state.model_copy(update={"interview_metrics": metrics})

    assert updated.interview_metrics is not None
    assert updated.interview_metrics.total_calls == 1
    assert state.interview_metrics is None
