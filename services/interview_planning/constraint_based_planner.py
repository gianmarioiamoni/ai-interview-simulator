# services/interview_planning/constraint_based_planner.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_planning.planning_result import PlanningResult
from services.interview_selection.selected_question import SelectedQuestion
from services.planning.planner_selection_scoring_engine import PlannerSelectionScoringEngine
from services.planning.contracts.planner_score_breakdown import PlannerScoreBreakdown
from services.telemetry.planner.planner_telemetry_builder import PlannerTelemetryBuilder
from services.interview_planning.contracts.planning_artifacts import PlanningArtifacts
from services.planning.contracts.planner_candidate_evaluation import PlannerCandidateEvaluation


from app.core.logger import get_logger

logger = get_logger(__name__)


class ConstraintBasedPlanner:

    MINIMUM_CANDIDATE_SCORE = 0.0

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._planner_scoring_engine = PlannerSelectionScoringEngine()

        self._telemetry_builder = PlannerTelemetryBuilder()

    # =====================================================
    # PUBLIC
    # =====================================================

    def plan(
        self,
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> PlanningResult:

        selected: list[SelectedQuestion] = []

        area_counts = defaultdict(int)

        # -------------------------------------------------
        # REQUIRED AREAS FIRST
        # -------------------------------------------------

        for area in constraints.required_areas:

            candidates = [item for item in items if (item.area.value == area)]

            if not candidates:
                continue

            best_candidate: QuestionBankItem | None = None

            best_breakdown: PlannerScoreBreakdown | None = None

            best_score = -1.0

            current_selected = [s.item for s in selected]

            for candidate in candidates:

                breakdown = self._planner_scoring_engine.score(
                    candidate=candidate,
                    selected_questions=(current_selected),
                )

                score = breakdown.final_score

                if score > best_score:

                    best_candidate = candidate

                    best_breakdown = breakdown

                    best_score = score

            if best_candidate is None or best_breakdown is None:
                continue

            selected.append(
                SelectedQuestion(
                    item=best_candidate,
                    selection_score=(best_score),
                    selection_reason=("required_area_selection"),
                    score_breakdown=(best_breakdown),
                )
            )

            area_counts[area] += 1

        # -------------------------------------------------
        # FILL REMAINING
        # -------------------------------------------------

        selected_ids = {q.item.id for q in selected}

        remaining = sorted(
            [item for item in items if (item.id not in selected_ids)],
            key=lambda q: (q.difficulty),
            reverse=True,
        )

        for item in remaining:

            area = item.area.value

            if area in constraints.excluded_areas:
                continue

            if area_counts[area] >= constraints.max_questions_per_area:
                continue

            current_selected = [s.item for s in selected]

            breakdown = self._planner_scoring_engine.score(
                candidate=item,
                selected_questions=(current_selected),
            )

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=(breakdown.final_score),
                    selection_reason=("constraint_fill"),
                    score_breakdown=(breakdown),
                )
            )

            area_counts[area] += 1

            if len(selected) >= constraints.minimum_total_questions:
                break

        average_difficulty = sum(q.item.difficulty for q in selected) / max(
            len(selected),
            1,
        )

        satisfied = []

        violated = []

        # -------------------------------------------------
        # REQUIRED AREAS
        # -------------------------------------------------

        selected_areas = {q.item.area.value for q in selected}

        for area in constraints.required_areas:

            if area in selected_areas:

                satisfied.append(f"required_area:{area}")

            else:

                violated.append(f"required_area:{area}")

        # -------------------------------------------------
        # MIN DIFFICULTY
        # -------------------------------------------------

        if average_difficulty >= constraints.minimum_average_difficulty:

            satisfied.append("minimum_average_difficulty")

        else:

            violated.append("minimum_average_difficulty")

        # -------------------------------------------------
        # FEASIBILITY COMPLETION
        # -------------------------------------------------

        selected_questions = self._fill_remaining_slots(
            selected=selected,
            available=items,
            constraints=constraints,
        )

        # -------------------------------------------------
        # TELEMETRY
        # -------------------------------------------------

        telemetry = self._telemetry_builder.build(
            selected_questions=selected_questions,
            total_candidates=len(items),
        )

        artifacts = PlanningArtifacts(
            telemetry=telemetry,
            planner_version="1.0.0",
            optimization_strategy="constraint_based",
        )

        return PlanningResult(
            selected_questions=(selected_questions),
            satisfied_constraints=(satisfied),
            violated_constraints=(violated),
            average_difficulty=round(
                average_difficulty,
                2,
            ),
            artifacts=artifacts,
        )

    # =====================================================
    # FEASIBILITY
    # =====================================================

    def _fill_remaining_slots(
        self,
        selected: list[SelectedQuestion],
        available: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> list[SelectedQuestion]:

        # -------------------------------------------------
        # EARLY EXIT
        # -------------------------------------------------

        if len(selected) >= constraints.minimum_total_questions:

            return selected

        selected_ids = {item.item.id for item in selected}

        remaining = []

        for item in available:

            if item.id in selected_ids:
                continue

            remaining.append(item)

        # -------------------------------------------------
        # SORT BY SCORE
        # -------------------------------------------------

        logger.info("Evaluating fallback candidates...")

        current_selected = [s.item for s in selected]

        scored_remaining: list[PlannerCandidateEvaluation] = []

        for candidate in remaining:

            breakdown = self._planner_scoring_engine.score(
                candidate=candidate,
                selected_questions=(current_selected),
            )

            scored_remaining.append(
                PlannerCandidateEvaluation(
                    candidate=candidate,
                    breakdown=breakdown,
                    final_score=breakdown.final_score,
                )
            )

        scored_remaining.sort(
            key=lambda x: (x.final_score),
            reverse=True,
        )

        # -------------------------------------------------
        # FILL
        # -------------------------------------------------

        for evaluation in scored_remaining:

            item = evaluation.candidate

            score = evaluation.final_score

            breakdown = evaluation.breakdown

            if len(selected) >= constraints.minimum_total_questions:
                break

            # -------------------------------------------------
            # QUALITY THRESHOLD
            # -------------------------------------------------

            if score < self.MINIMUM_CANDIDATE_SCORE:

                logger.info(f"Rejected low-quality candidate: {item.text}")

                logger.info(f"Score: {score}")

                continue

            logger.info(f"Selected fallback candidate: {item.text}")

            logger.info(f"Score: {score}")

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=(score),
                    selection_reason=("fallback_completion"),
                    score_breakdown=(breakdown),
                )
            )

        return selected

