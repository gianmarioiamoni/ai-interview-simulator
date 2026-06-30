# tests/services/interview_reasoner/pattern_detection/test_registry.py

import pytest

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry
from services.interview_reasoner.pattern_detection.registry_errors import (
    CyclicDependencyError,
    DuplicateDetectorError,
    MissingDependencyError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_detector(
    name: str,
    priority: int = 100,
    enabled: bool = True,
    dependencies: list[str] | None = None,
) -> PatternDetector:
    meta = DetectorMetadata(
        name=name,
        priority=priority,
        enabled=enabled,
        dependencies=dependencies or [],
    )

    class _D(PatternDetector):
        @property
        def metadata(self) -> DetectorMetadata:
            return meta

        def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
            return DetectorResult(detector_name=name)

    return _D()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_single():
    reg = PatternDetectorRegistry()
    d = _make_detector("A")
    reg.register(d)
    assert reg.exists("A")


def test_register_duplicate_raises():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    with pytest.raises(DuplicateDetectorError) as exc_info:
        reg.register(_make_detector("A"))
    assert exc_info.value.name == "A"


def test_unregister_removes_detector():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    reg.unregister("A")
    assert not reg.exists("A")


def test_unregister_nonexistent_is_noop():
    reg = PatternDetectorRegistry()
    reg.unregister("NOTEXIST")  # must not raise


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def test_exists_false_for_unknown():
    reg = PatternDetectorRegistry()
    assert not reg.exists("UNKNOWN")


def test_by_name_returns_detector():
    reg = PatternDetectorRegistry()
    d = _make_detector("A")
    reg.register(d)
    assert reg.by_name("A") is d


def test_by_name_returns_none_for_unknown():
    reg = PatternDetectorRegistry()
    assert reg.by_name("X") is None


def test_all_returns_registered():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    reg.register(_make_detector("B"))
    names = {d.metadata.name for d in reg.all()}
    assert names == {"A", "B"}


def test_enabled_excludes_disabled():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A", enabled=True))
    reg.register(_make_detector("B", enabled=False))
    names = [d.metadata.name for d in reg.enabled()]
    assert "A" in names
    assert "B" not in names


def test_enabled_empty_registry():
    assert PatternDetectorRegistry().enabled() == []


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

def test_ordered_by_priority():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("C", priority=30))
    reg.register(_make_detector("A", priority=10))
    reg.register(_make_detector("B", priority=20))
    names = [d.metadata.name for d in reg.ordered()]
    assert names == ["A", "B", "C"]


def test_ordered_stable_equal_priority():
    """Two detectors with equal priority must both appear."""
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("X", priority=5))
    reg.register(_make_detector("Y", priority=5))
    names = {d.metadata.name for d in reg.ordered()}
    assert names == {"X", "Y"}


# ---------------------------------------------------------------------------
# Dependency validation
# ---------------------------------------------------------------------------

def test_missing_dependency_raises():
    reg = PatternDetectorRegistry()
    with pytest.raises(MissingDependencyError) as exc_info:
        reg.register(_make_detector("B", dependencies=["A"]))
    assert exc_info.value.detector_name == "B"
    assert exc_info.value.missing_dependency == "A"


def test_satisfied_dependency_ok():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    reg.register(_make_detector("B", dependencies=["A"]))
    assert reg.exists("B")


def test_chain_dependency_ok():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    reg.register(_make_detector("B", dependencies=["A"]))
    reg.register(_make_detector("C", dependencies=["B"]))
    assert reg.exists("C")


# ---------------------------------------------------------------------------
# Cycle detection
# ---------------------------------------------------------------------------

def test_self_cycle_raises():
    reg = PatternDetectorRegistry()
    with pytest.raises((MissingDependencyError, CyclicDependencyError)):
        reg.register(_make_detector("A", dependencies=["A"]))


def test_two_node_cycle_missing_dep_first():
    """When B is not yet registered, A→B raises MissingDependencyError before cycle check."""
    reg = PatternDetectorRegistry()
    with pytest.raises(MissingDependencyError) as exc_info:
        reg.register(_make_detector("A", dependencies=["B"]))
    assert exc_info.value.missing_dependency == "B"


def test_explicit_cycle_after_registration():
    """Register A, then B→A, then unregister A and register A→B (creates A↔B cycle)."""
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A", priority=1))
    reg.register(_make_detector("B", priority=2, dependencies=["A"]))
    reg.unregister("A")
    with pytest.raises(CyclicDependencyError):
        reg.register(_make_detector("A", dependencies=["B"]))
    # After failed registration, A must not be in registry
    assert not reg.exists("A")


def test_three_node_cycle_raises():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("A"))
    reg.register(_make_detector("B", dependencies=["A"]))
    reg.register(_make_detector("C", dependencies=["B"]))
    reg.unregister("A")
    with pytest.raises(CyclicDependencyError):
        reg.register(_make_detector("A", dependencies=["C"]))
    assert not reg.exists("A")


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

def test_duplicate_error_message():
    err = DuplicateDetectorError("MyDetector")
    assert "MyDetector" in str(err)


def test_missing_dependency_error_message():
    err = MissingDependencyError("B", "A")
    assert "B" in str(err)
    assert "A" in str(err)


def test_cyclic_dependency_error_message():
    err = CyclicDependencyError(["A", "B", "A"])
    assert "A" in str(err)
    assert "B" in str(err)
    assert err.cycle == ["A", "B", "A"]


# ---------------------------------------------------------------------------
# Base detector contract
# ---------------------------------------------------------------------------

def test_base_detector_cannot_be_instantiated():
    from services.interview_reasoner.pattern_detection.base_detector import PatternDetector as PD
    with pytest.raises(TypeError):
        PD()  # type: ignore[abstract]


def test_concrete_detector_returns_result():
    d = _make_detector("Concrete")
    inp = ReasonerInput(session_id="s", question_index=0)
    result = d.detect(inp)
    assert result.detector_name == "Concrete"
    assert result.generated_signals == []
