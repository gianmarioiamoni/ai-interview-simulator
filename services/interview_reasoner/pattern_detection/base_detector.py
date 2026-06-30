# services/interview_reasoner/pattern_detection/base_detector.py

from abc import ABC, abstractmethod

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata


class PatternDetector(ABC):
    """Abstract base for all pattern detectors (ADR-034, ADR-045).

    Concrete detectors must implement:
        metadata → DetectorMetadata
        detect(input) → DetectorResult

    Detectors are stateless — all state is derived from ReasonerInput.
    No LLM calls permitted (ADR-028).
    """

    @property
    @abstractmethod
    def metadata(self) -> DetectorMetadata:
        """Return the metadata descriptor for this detector."""

    @abstractmethod
    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        """Run pattern detection and return a DetectorResult.

        Must be:
          - deterministic
          - side-effect-free
          - O(n) relative to session history size
          - no LLM calls

        `DetectorResult.execution_time_ms` is populated by the pipeline.
        """
