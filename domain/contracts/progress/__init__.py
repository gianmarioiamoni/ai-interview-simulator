# domain/contracts/progress/__init__.py
# Progress Layer — ADR-016A + ADR-022 contracts (EPIC-04, E04-M2, Sprint 11B)

from domain.contracts.progress.learning_progress import (
    DimensionalScore,
    LearningProgress,
    SessionProgressEntry,
)
from domain.contracts.progress.learning_progress_builder import LearningProgressBuilder
from domain.contracts.progress.learning_progress_statistics import (
    DimensionalTrend,
    LearningProgressStatistics,
)
from domain.contracts.progress.learning_progress_summary import LearningProgressSummary
from domain.contracts.progress.learning_progress_validator import (
    LearningProgressValidationResult,
    LearningProgressValidator,
)
from domain.contracts.progress.progress_comparison import (
    DimensionalDelta,
    ProgressComparison,
)

__all__ = [
    "DimensionalScore",
    "LearningProgress",
    "SessionProgressEntry",
    "LearningProgressBuilder",
    "DimensionalTrend",
    "LearningProgressStatistics",
    "LearningProgressSummary",
    "LearningProgressValidator",
    "LearningProgressValidationResult",
    "DimensionalDelta",
    "ProgressComparison",
]
