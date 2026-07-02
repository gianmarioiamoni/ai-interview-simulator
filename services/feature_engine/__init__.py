# services/feature_engine/__init__.py
# Feature Engine — Knowledge Construction Engine (ADR-018, ADR-020, E01-M2)

from services.feature_engine.feature_engine_context import FeatureEngineContext
from services.feature_engine.feature_engine_result import FeatureEngineResult
from services.feature_engine.feature_engine_metrics import (
    FeatureEngineMetrics,
    UpdaterTimingRecord,
)
from services.feature_engine.feature_engine_diagnostics import (
    FeatureEngineDiagnostics,
    UpdaterInvocationRecord,
)
from services.feature_engine.feature_resolution_report import (
    CandidateResolutionRecord,
    FeatureResolutionRecord,
    FeatureResolutionReport,
    ResolutionStrategy,
)
from services.feature_engine.feature_update_plan import (
    FeatureUpdatePlan,
    UpdaterInvocationSpec,
)
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from services.feature_engine.incremental_feature_engine import IncrementalFeatureEngine
from services.feature_engine.replay_feature_engine import ReplayFeatureEngine

__all__ = [
    "FeatureEngineContext",
    "FeatureEngineResult",
    "FeatureEngineMetrics",
    "UpdaterTimingRecord",
    "FeatureEngineDiagnostics",
    "UpdaterInvocationRecord",
    "CandidateResolutionRecord",
    "FeatureResolutionRecord",
    "FeatureResolutionReport",
    "ResolutionStrategy",
    "FeatureUpdatePlan",
    "UpdaterInvocationSpec",
    "FeatureEngine",
    "FeatureEngineError",
    "IncrementalFeatureEngine",
    "ReplayFeatureEngine",
]
