# tests/domain/observation/runtime/test_runtime_architecture.py
# Architecture invariants: no forbidden dependencies, correct layer boundaries.

from __future__ import annotations

import importlib
import inspect
import sys


RUNTIME_MODULES = [
    "domain.observation.runtime.observation_batch",
    "domain.observation.runtime.observation_cursor",
    "domain.observation.runtime.observation_ordering",
    "domain.observation.runtime.observation_collection",
    "domain.observation.runtime.observation_statistics",
    "domain.observation.runtime.observation_delta",
    "domain.observation.runtime.observation_store_query_engine",
]

FORBIDDEN_IMPORTS = [
    "services.feature_engine",
    "domain.profile",
    "domain.contracts.feature",
    "services.narrative",
    "services.coaching",
    "domain.contracts.language",
    "infrastructure",
]


class TestRuntimeLayerBoundaries:
    def test_no_forbidden_imports(self):
        violations: list[str] = []
        for module_name in RUNTIME_MODULES:
            mod = importlib.import_module(module_name)
            source = inspect.getsource(mod)
            for forbidden in FORBIDDEN_IMPORTS:
                if forbidden in source:
                    violations.append(f"{module_name} imports {forbidden}")
        assert not violations, f"Layer boundary violations:\n" + "\n".join(violations)

    def test_all_runtime_modules_importable(self):
        for module_name in RUNTIME_MODULES:
            mod = importlib.import_module(module_name)
            assert mod is not None

    def test_runtime_package_exports_all_objects(self):
        from domain.observation.runtime import (
            ObservationBatch,
            ObservationCursor,
            ObservationOrdering,
            ObservationOrderingPolicy,
            ObservationCollection,
            ObservationStatistics,
            ObservationDelta,
            ObservationStoreQueryEngine,
        )
        # All symbols must be importable without error — reaching here is the assertion.

    def test_observation_batch_is_frozen_pydantic(self):
        from domain.observation.runtime.observation_batch import ObservationBatch
        from pydantic import BaseModel
        assert issubclass(ObservationBatch, BaseModel)
        assert ObservationBatch.model_config.get("frozen") is True

    def test_observation_statistics_is_frozen_pydantic(self):
        from domain.observation.runtime.observation_statistics import ObservationStatistics
        from pydantic import BaseModel
        assert issubclass(ObservationStatistics, BaseModel)
        assert ObservationStatistics.model_config.get("frozen") is True

    def test_observation_delta_is_frozen_pydantic(self):
        from domain.observation.runtime.observation_delta import ObservationDelta
        from pydantic import BaseModel
        assert issubclass(ObservationDelta, BaseModel)
        assert ObservationDelta.model_config.get("frozen") is True

    def test_observation_cursor_is_not_pydantic(self):
        from domain.observation.runtime.observation_cursor import ObservationCursor
        from pydantic import BaseModel
        assert not issubclass(ObservationCursor, BaseModel)

    def test_query_engine_does_not_expose_append(self):
        from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
        assert not hasattr(ObservationStoreQueryEngine, "append"), (
            "QueryEngine must be read-only; append() must not be exposed"
        )
