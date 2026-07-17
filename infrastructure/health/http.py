# infrastructure/health/http.py
#
# EPIC-08 P4/C10 — infra serialization for readiness HTTP (IB-03; not domain models).

from __future__ import annotations

from infrastructure.health.types import ProbeResult, ReadinessReport

READINESS_PATH = "/health/ready"


def readiness_status_code(report: ReadinessReport) -> int:
    """HTTP status: 200 when ready, 503 when any enabled probe failed."""
    return 200 if report.ready else 503


def readiness_response_body(report: ReadinessReport) -> dict[str, object]:
    return {
        "ready": report.ready,
        "probes": [_probe_body(probe) for probe in report.probes],
    }


def _probe_body(probe: ProbeResult) -> dict[str, object]:
    return {
        "name": probe.name,
        "status": probe.status,
        "detail": probe.detail,
        "error_type": probe.error_type,
        "duration_ms": probe.duration_ms,
    }
