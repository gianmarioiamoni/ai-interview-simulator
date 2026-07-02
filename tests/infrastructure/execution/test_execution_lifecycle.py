# tests/infrastructure/execution/test_execution_lifecycle.py

import time
import pytest

from infrastructure.execution.execution_lifecycle import ExecutionLifecycle, ExecutionPhase
from infrastructure.execution.contracts.execution_status import ExecutionStatus
from infrastructure.execution.contracts.execution_result import ExecutionResult


@pytest.fixture
def lifecycle() -> ExecutionLifecycle:
    return ExecutionLifecycle()


@pytest.fixture
def sample_result() -> ExecutionResult:
    return ExecutionResult(
        execution_id="exec-001",
        language_id="python",
        question_id="q-001",
        status=ExecutionStatus.SUCCESS,
    )


class TestExecutionPhaseEnum:
    def test_all_phases_exist(self):
        assert ExecutionPhase.PRE_VALIDATION
        assert ExecutionPhase.DISPATCH
        assert ExecutionPhase.POST_PROCESSING
        assert ExecutionPhase.COMPLETE
        assert ExecutionPhase.FAILED

    def test_phases_are_string_enum(self):
        assert isinstance(ExecutionPhase.PRE_VALIDATION, str)

    def test_phase_values(self):
        assert ExecutionPhase.PRE_VALIDATION == "pre_validation"
        assert ExecutionPhase.DISPATCH == "dispatch"
        assert ExecutionPhase.COMPLETE == "complete"
        assert ExecutionPhase.FAILED == "failed"


class TestLifecycleInitialState:
    def test_initial_phase_is_pre_validation(self, lifecycle):
        assert lifecycle.current_phase == ExecutionPhase.PRE_VALIDATION

    def test_initial_is_complete_false(self, lifecycle):
        assert lifecycle.is_complete is False

    def test_initial_elapsed_ms_non_negative(self, lifecycle):
        assert lifecycle.elapsed_ms >= 0


class TestLifecycleStart:
    def test_start_records_time(self, lifecycle):
        lifecycle.start()
        assert lifecycle.elapsed_ms >= 0

    def test_start_records_transition(self, lifecycle):
        lifecycle.start()
        assert len(lifecycle.transitions) >= 1

    def test_start_phase_remains_pre_validation(self, lifecycle):
        lifecycle.start()
        assert lifecycle.current_phase == ExecutionPhase.PRE_VALIDATION


class TestLifecycleTransitions:
    def test_transition_changes_current_phase(self, lifecycle):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        assert lifecycle.current_phase == ExecutionPhase.DISPATCH

    def test_transition_records_history(self, lifecycle):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        phases = [t[0] for t in lifecycle.transitions]
        assert ExecutionPhase.DISPATCH in phases

    def test_multiple_transitions(self, lifecycle):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        lifecycle.transition(ExecutionPhase.POST_PROCESSING)
        assert lifecycle.current_phase == ExecutionPhase.POST_PROCESSING

    def test_transitions_ordered(self, lifecycle):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        lifecycle.transition(ExecutionPhase.POST_PROCESSING)
        times = [t[1] for t in lifecycle.transitions]
        assert times == sorted(times)

    def test_transition_timestamps_monotonic(self, lifecycle):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.DISPATCH)
        time.sleep(0.001)
        lifecycle.transition(ExecutionPhase.POST_PROCESSING)
        transitions = lifecycle.transitions
        assert transitions[-1][1] >= transitions[-2][1]


class TestLifecycleComplete:
    def test_complete_sets_is_complete(self, lifecycle, sample_result):
        lifecycle.start()
        lifecycle.complete(sample_result)
        assert lifecycle.is_complete is True

    def test_complete_transitions_to_complete_phase(self, lifecycle, sample_result):
        lifecycle.start()
        lifecycle.complete(sample_result)
        assert lifecycle.current_phase == ExecutionPhase.COMPLETE

    def test_complete_records_transition(self, lifecycle, sample_result):
        lifecycle.start()
        lifecycle.complete(sample_result)
        phases = [t[0] for t in lifecycle.transitions]
        assert ExecutionPhase.COMPLETE in phases

    def test_elapsed_ms_positive_after_complete(self, lifecycle, sample_result):
        lifecycle.start()
        lifecycle.complete(sample_result)
        assert lifecycle.elapsed_ms >= 0


class TestLifecycleFail:
    def test_fail_sets_is_complete(self, lifecycle):
        lifecycle.start()
        lifecycle.fail("something went wrong")
        assert lifecycle.is_complete is True

    def test_fail_transitions_to_failed_phase(self, lifecycle):
        lifecycle.start()
        lifecycle.fail("error")
        assert lifecycle.current_phase == ExecutionPhase.FAILED

    def test_fail_records_transition(self, lifecycle):
        lifecycle.start()
        lifecycle.fail("error")
        phases = [t[0] for t in lifecycle.transitions]
        assert ExecutionPhase.FAILED in phases


class TestLifecycleElapsed:
    def test_elapsed_increases_over_time(self, lifecycle):
        lifecycle.start()
        t1 = lifecycle.elapsed_ms
        time.sleep(0.01)
        t2 = lifecycle.elapsed_ms
        assert t2 > t1

    def test_elapsed_ms_is_float(self, lifecycle):
        lifecycle.start()
        assert isinstance(lifecycle.elapsed_ms, float)


class TestLifecycleFullFlow:
    def test_full_pipeline_flow(self, lifecycle, sample_result):
        lifecycle.start()
        lifecycle.transition(ExecutionPhase.PRE_VALIDATION)
        lifecycle.transition(ExecutionPhase.DISPATCH)
        lifecycle.transition(ExecutionPhase.POST_PROCESSING)
        lifecycle.complete(sample_result)
        assert lifecycle.current_phase == ExecutionPhase.COMPLETE
        assert lifecycle.is_complete

    def test_transitions_returns_copy(self, lifecycle):
        lifecycle.start()
        t1 = lifecycle.transitions
        lifecycle.transition(ExecutionPhase.DISPATCH)
        t2 = lifecycle.transitions
        assert len(t1) != len(t2)
