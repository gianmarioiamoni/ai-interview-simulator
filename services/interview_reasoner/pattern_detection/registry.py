# services/interview_reasoner/pattern_detection/registry.py

from __future__ import annotations

from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.registry_errors import (
    CyclicDependencyError,
    DuplicateDetectorError,
    MissingDependencyError,
)


class PatternDetectorRegistry:
    """Metadata-driven registry for PatternDetectors (ADR-034, ADR-045).

    Ordering is derived from DetectorMetadata.priority (ascending).
    Dependency validation is performed eagerly on registration.
    No hardcoded if/else logic — all behaviour driven by DetectorMetadata.
    """

    def __init__(self) -> None:
        self._detectors: dict[str, PatternDetector] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, detector: PatternDetector) -> None:
        """Register a detector.

        Raises:
            DuplicateDetectorError: if a detector with the same name is already registered.
            MissingDependencyError: if any declared dependency is not registered.
            CyclicDependencyError: if registration would introduce a dependency cycle.
        """
        name = detector.metadata.name
        if name in self._detectors:
            raise DuplicateDetectorError(name)

        self._validate_dependencies(detector)

        # Tentatively add, then check for cycles including this new node.
        self._detectors[name] = detector
        try:
            self._validate_no_cycles()
        except CyclicDependencyError:
            del self._detectors[name]
            raise

    def unregister(self, name: str) -> None:
        """Remove a detector by name. No-op if not found."""
        self._detectors.pop(name, None)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def enabled(self) -> list[PatternDetector]:
        """Return all enabled detectors in priority order."""
        return [d for d in self.ordered() if d.metadata.enabled]

    def ordered(self) -> list[PatternDetector]:
        """Return all detectors sorted by priority ascending."""
        return sorted(self._detectors.values(), key=lambda d: d.metadata.priority)

    def by_name(self, name: str) -> PatternDetector | None:
        """Return the detector with the given name, or None."""
        return self._detectors.get(name)

    def exists(self, name: str) -> bool:
        """Return True if a detector with the given name is registered."""
        return name in self._detectors

    def all(self) -> list[PatternDetector]:
        """Return all registered detectors (enabled and disabled), in priority order."""
        return self.ordered()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_dependencies(self, detector: PatternDetector) -> None:
        for dep in detector.metadata.dependencies:
            if dep not in self._detectors:
                raise MissingDependencyError(detector.metadata.name, dep)

    def _validate_no_cycles(self) -> None:
        """Detect cycles using iterative DFS with a grey/black colour scheme."""
        WHITE, GREY, BLACK = 0, 1, 2
        colour: dict[str, int] = {name: WHITE for name in self._detectors}

        def dfs(node: str, path: list[str]) -> None:
            colour[node] = GREY
            path.append(node)
            for dep in self._detectors[node].metadata.dependencies:
                if dep not in colour:
                    continue
                if colour[dep] == GREY:
                    cycle_start = path.index(dep)
                    raise CyclicDependencyError(path[cycle_start:] + [dep])
                if colour[dep] == WHITE:
                    dfs(dep, path)
            path.pop()
            colour[node] = BLACK

        for name in list(self._detectors):
            if colour[name] == WHITE:
                dfs(name, [])
