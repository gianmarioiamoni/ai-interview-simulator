# services/interview_planning/builders/planning_artifacts_builder.py

from services.interview_selection.selected_question import SelectedQuestion
from services.interview_planning.contracts.planning_artifacts import PlanningArtifacts
from services.telemetry.planner.planner_telemetry_builder import PlannerTelemetryBuilder


class PlanningArtifactsBuilder:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._telemetry_builder = PlannerTelemetryBuilder()

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        selected_questions: list[SelectedQuestion],
        total_candidates: int,
    ) -> PlanningArtifacts:

        telemetry = self._telemetry_builder.build(
            selected_questions=selected_questions,
            total_candidates=total_candidates,
        )

        return PlanningArtifacts(
            telemetry=telemetry,
            planner_version="1.0.0",
            optimization_strategy="constraint_based",
        )
