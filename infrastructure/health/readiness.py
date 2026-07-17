# infrastructure/health/readiness.py
#
# EPIC-08 P4/C9 — aggregate readiness evaluation (infra only; no HTTP wiring yet).

from __future__ import annotations

from infrastructure.config.settings import Settings, settings as default_settings
from infrastructure.health.probes import (
    LLMConnectivityCheck,
    probe_database,
    probe_llm,
    probe_sandbox,
)
from infrastructure.health.types import ReadinessReport


def evaluate_readiness(
    settings: Settings | None = None,
    *,
    llm_connectivity_check: LLMConnectivityCheck | None = None,
) -> ReadinessReport:
    """
    Run HLT-01 probes and return aggregate readiness.

    Overall ready iff no enabled probe reports failure (skipped is allowed).
    """
    resolved = settings if settings is not None else default_settings
    probes = (
        probe_llm(resolved, connectivity_check=llm_connectivity_check),
        probe_database(resolved),
        probe_sandbox(resolved),
    )
    ready = all(probe.status != "failure" for probe in probes)
    return ReadinessReport(ready=ready, probes=probes)
