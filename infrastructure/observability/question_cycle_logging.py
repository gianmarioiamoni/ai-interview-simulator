# infrastructure/observability/question_cycle_logging.py
#
# EPIC-V13-09 C2 — optional question-cycle span emit via existing EPIC-08 Freeze
# §6.1 schema fields only (AR-02, AR-10, MEAS-03, OBS-01/03/05).

from __future__ import annotations

import logging

from infrastructure.observability.structured_log import emit_structured_log

# Cycle-oriented event name allowed by OBS-03 / AR-10 — not a new schema field.
QUESTION_CYCLE_EVENT = "question_cycle.complete"
QUESTION_CYCLE_COMPONENT = "harness"


def emit_question_cycle_structured_log(
    *,
    duration_ms: float | int,
    session_id: str | None = None,
    execution_id: str | None = None,
    status: str = "success",
    level: str = "INFO",
    error_type: str | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, object]:
    """
    Optionally emit a written-question-cycle wall-clock span.

    Uses only existing Freeze fields: ``event``, ``duration_ms``, ``session_id``,
    ``execution_id``, plus required schema keys. Observational only — emission
    failures are absorbed by ``emit_structured_log``; does not alter caller
    control flow or swallow application exceptions (OBS-01/03/05).
    """
    resolved_level = "ERROR" if status == "failure" and level == "INFO" else level
    return emit_structured_log(
        event=QUESTION_CYCLE_EVENT,
        component=QUESTION_CYCLE_COMPONENT,
        status=status,
        level=resolved_level,
        session_id=session_id,
        execution_id=execution_id,
        duration_ms=duration_ms,
        error_type=error_type,
        logger=logger,
    )
