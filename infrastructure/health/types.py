# infrastructure/health/types.py
#
# EPIC-08 P4/C9 — infrastructure readiness contracts (IB-03; not domain frozen models).

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProbeResult:
    name: str
    status: str  # success | failure | skipped
    detail: str | None = None
    error_type: str | None = None
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ready: bool
    probes: tuple[ProbeResult, ...]

    def probe_by_name(self, name: str) -> ProbeResult | None:
        for probe in self.probes:
            if probe.name == name:
                return probe
        return None
