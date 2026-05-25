# services/planning/planner_telemetry_builder.py

from collections import defaultdict
from statistics import mean

from services.interview_selection.selected_question import SelectedQuestion
from services.telemetry.planner.planner_telemetry import PlannerTelemetry
from services.planning.difficulty_progression_analyzer import DifficultyProgressionAnalyzer
from services.planning.difficulty_spike_suppressor import DifficultySpikeSuppressor


class PlannerTelemetryBuilder:


    def __init__(self) -> None:
        self._difficulty_progression_analyzer = DifficultyProgressionAnalyzer()
        self._difficulty_spike_suppressor = DifficultySpikeSuppressor()


    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        selected_questions: list[SelectedQuestion],
        total_candidates: int,
    ) -> PlannerTelemetry:

        if not selected_questions:

            return PlannerTelemetry(
                total_candidates=total_candidates,
                selected_candidates=0,
                rejected_candidates=total_candidates,
                average_selection_score=0.0,
                average_difficulty=0.0,
                semantic_penalty_count=0,
                novelty_bonus_count=0,
                rarity_bonus_count=0,
                unique_areas=0,
                area_distribution={},
                rationale_distribution={},
            )

        # -------------------------------------------------
        # COUNTERS
        # -------------------------------------------------

        area_distribution = defaultdict(int)

        rationale_distribution = defaultdict(int)

        semantic_penalty_count = 0

        novelty_bonus_count = 0

        rarity_bonus_count = 0

        difficulty_spike_penalty_count = 0

        # -------------------------------------------------
        # ITERATION
        # -------------------------------------------------

        for question in selected_questions:

            item = question.item

            breakdown = question.score_breakdown

            area_distribution[item.area.value] += 1

            for rationale in breakdown.rationale:

                rationale_distribution[rationale] += 1

            if breakdown.cluster_penalty < 0:
                semantic_penalty_count += 1

            if breakdown.novelty_bonus > 0:
                novelty_bonus_count += 1

            if breakdown.category_rarity_bonus > 0:
                rarity_bonus_count += 1

            if breakdown.difficulty_spike_penalty < 0:
                difficulty_spike_penalty_count += 1

        # -------------------------------------------------
        # AGGREGATIONS
        # -------------------------------------------------

        average_selection_score = round(
            mean(q.selection_score for q in selected_questions),
            4,
        )

        average_difficulty = round(
            mean(q.item.difficulty for q in selected_questions),
            4,
        )

        difficulty_progression_score = self._difficulty_progression_analyzer.calculate_progression_score(
           [q.item for q in selected_questions],
        )

        # -------------------------------------------------
        # BUILD
        # -------------------------------------------------

        return PlannerTelemetry(
            total_candidates=(total_candidates),
            selected_candidates=(len(selected_questions)),
            rejected_candidates=(total_candidates - len(selected_questions)),
            average_selection_score=(average_selection_score),
            average_difficulty=(average_difficulty),
            semantic_penalty_count=(semantic_penalty_count),
            novelty_bonus_count=(novelty_bonus_count),
            rarity_bonus_count=(rarity_bonus_count),
            unique_areas=(len(area_distribution)),
            area_distribution=dict(area_distribution),
            rationale_distribution=dict(rationale_distribution),
            difficulty_spike_penalty_count=(difficulty_spike_penalty_count),
            difficulty_progression_score=(difficulty_progression_score),
        )
