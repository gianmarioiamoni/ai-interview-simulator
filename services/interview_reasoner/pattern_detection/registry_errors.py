# services/interview_reasoner/pattern_detection/registry_errors.py

class RegistryError(Exception):
    """Base class for all PatternDetectorRegistry errors."""


class DuplicateDetectorError(RegistryError):
    """Raised when a detector with the same name is registered twice."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Detector '{name}' is already registered.")
        self.name = name


class MissingDependencyError(RegistryError):
    """Raised when a registered detector declares a dependency that is not registered."""

    def __init__(self, detector_name: str, missing_dependency: str) -> None:
        super().__init__(
            f"Detector '{detector_name}' depends on '{missing_dependency}', "
            "which is not registered."
        )
        self.detector_name = detector_name
        self.missing_dependency = missing_dependency


class CyclicDependencyError(RegistryError):
    """Raised when a cyclic dependency is detected among registered detectors."""

    def __init__(self, cycle: list[str]) -> None:
        path = " → ".join(cycle)
        super().__init__(f"Cyclic dependency detected: {path}")
        self.cycle = cycle
