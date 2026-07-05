# app/graph/nodes/report_node.py
"""ReportNode (PAT-06: LangGraph sole orchestrator).

Responsibilities (orchestration only):
1. Guard: return immediately if session_history is None (no-op; session not closed).
2. Consume state.session_history — no recomputation.
3. Assemble Report via ReportBuilder.with_session_history() (PAT-05).
4. Write state.report (sole writer).
5. Clear processing flags (is_processing, current_step).

Constraints (ADR-022, ADR-032):
- Zero FeatureEngine executions.
- Zero KnowledgePipeline executions.
- Zero ObservationExtractor executions.
- No NarrativeGenerator, no CoachingEngine.
- Pure projection from SessionHistory.
- Non-fatal: any assembly failure logs a warning; flags still cleared.
"""

from __future__ import annotations

from domain.contracts.interview_state import InterviewState
from domain.contracts.report.report_builder import ReportBuilder
from app.core.logger import get_logger

logger = get_logger(__name__)


def report_node(state: InterviewState) -> InterviewState:
    """Assemble Report from SessionHistory. Sole writer of state.report."""
    if state.session_history is None:
        logger.debug("report_node: session_history not set — skipping report assembly")
        return state.model_copy(
            update={
                "is_processing": False,
                "current_step": None,
            }
        )

    try:
        report = ReportBuilder().with_session_history(state.session_history).build()
        logger.info(
            "report_node completed | session=%s candidate=%s features=%d",
            report.session_id,
            report.candidate_identity_id,
            report.feature_count,
        )
        return state.model_copy(
            update={
                "report": report,
                "is_processing": False,
                "current_step": None,
            }
        )

    except Exception as exc:
        logger.warning(
            "report_node assembly failed — report not set | session=%s error=%s",
            state.interview_id,
            type(exc).__name__,
        )
        return state.model_copy(
            update={
                "is_processing": False,
                "current_step": None,
            }
        )
