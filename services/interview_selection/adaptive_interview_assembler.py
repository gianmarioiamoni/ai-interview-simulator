# services/interview_selection/adaptive_interview_assembler.py

from collections import defaultdict

from services.interview_selection.assembled_question import AssembledQuestion
from services.interview_selection.adaptive_interview_result import AdaptiveInterviewResult
from services.interview_selection.interview_stage import InterviewStage
from services.interview_policy.interview_policy import InterviewPolicy
from services.interview_selection.selected_question import SelectedQuestion
from services.interview_selection.policy_scorer import PolicyScorer

_STAGE_BY_DIFFICULTY: dict[str, InterviewStage] = {}  # dynamic below

_STAGE_REASONS: dict[InterviewStage, str] = {
    InterviewStage.WARMUP: "warmup_progression",
    InterviewStage.CORE: "core_depth_evaluation",
    InterviewStage.ADVANCED: "advanced_signal_assessment",
}


def _assign_stage(difficulty: int) -> InterviewStage:
    if difficulty <= 2:
        return InterviewStage.WARMUP
    if difficulty <= 4:
        return InterviewStage.CORE
    return InterviewStage.ADVANCED


class AdaptiveInterviewAssembler:

    def __init__(self) -> None:
        self._scorer = PolicyScorer()

    # =====================================================
    # PUBLIC
    # =====================================================

    def assemble(
        self,
        items: list[SelectedQuestion],
        policy: InterviewPolicy,
        max_questions: int = 5,
    ) -> AdaptiveInterviewResult:

        sorted_items = sorted(
            items,
            key=lambda q: (self._scorer.score(q.item, policy), q.item.difficulty),
            reverse=True,
        )

        selected: list[AssembledQuestion] = []
        area_counts: dict[str, int] = defaultdict(int)

        for selected_question in sorted_items:
            if len(selected) >= max_questions:
                break

            item = selected_question.item
            area = item.area.value

            if area_counts[area] >= policy.max_questions_per_area:
                continue

            stage = _assign_stage(item.difficulty)

            selected.append(
                AssembledQuestion(
                    item=item,
                    stage=stage,
                    assembly_reason=_STAGE_REASONS[stage],
                    score_breakdown=selected_question.score_breakdown,
                    selection_score=selected_question.selection_score,
                    selection_reason=selected_question.selection_reason,
                )
            )

            area_counts[area] += 1

        coverage_score = len({q.item.area.value for q in selected}) / max(
            len({i.item.area.value for i in items}), 1
        )
        average_difficulty = sum(q.item.difficulty for q in selected) / max(
            len(selected), 1
        )
        progression_score = self._calculate_progression(selected)

        return AdaptiveInterviewResult(
            questions=selected,
            coverage_score=round(coverage_score, 2),
            average_difficulty=round(average_difficulty, 2),
            progression_score=round(progression_score, 2),
        )

    # =====================================================
    # PRIVATE
    # =====================================================

    @staticmethod
    def _calculate_progression(questions: list[AssembledQuestion]) -> float:
        difficulties = [q.item.difficulty for q in questions]
        if len(difficulties) < 2:
            return 1.0
        ordered_pairs = sum(
            1
            for i in range(len(difficulties) - 1)
            if difficulties[i] <= difficulties[i + 1]
        )
        return ordered_pairs / (len(difficulties) - 1)
