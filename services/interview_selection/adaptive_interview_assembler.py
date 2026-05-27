# services/interview_selection/adaptive_interview_assembler.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_selection.assembled_question import AssembledQuestion
from services.interview_selection.adaptive_interview_result import AdaptiveInterviewResult
from services.interview_selection.interview_stage import InterviewStage
from services.interview_policy.interview_policy import InterviewPolicy
from services.interview_selection.selected_question import SelectedQuestion


class AdaptiveInterviewAssembler:

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
            key=lambda q: (
                self._policy_score(
                    q.item,
                    policy,
                ),
                q.item.difficulty,
            ),
            reverse=True,
        )

        selected: list[AssembledQuestion] = []

        area_counts = defaultdict(int)

        for selected_question in sorted_items:

            if len(selected) >= max_questions:
                break

            item = selected_question.item

            area = item.area.value

            if area_counts[area] >= policy.max_questions_per_area:
                continue

            stage = self._assign_stage(
                item.difficulty,
            )

            selected.append(
                AssembledQuestion(
                    item=item,
                    stage=stage,
                    assembly_reason=(
                        self._build_reason(
                            stage,
                        )
                    ),
                    score_breakdown=(selected_question.score_breakdown),
                    selection_score=(selected_question.selection_score),
                    selection_reason=(selected_question.selection_reason),
                )
            )

            area_counts[area] += 1

        coverage_score = len({q.item.area.value for q in selected}) / max(
            len({i.item.area.value for i in items}),
            1,
        )

        average_difficulty = sum(q.item.difficulty for q in selected) / max(
            len(selected),
            1,
        )

        progression_score = self._calculate_progression(
            selected,
        )

        return AdaptiveInterviewResult(
            questions=selected,
            coverage_score=round(
                coverage_score,
                2,
            ),
            average_difficulty=round(
                average_difficulty,
                2,
            ),
            progression_score=round(
                progression_score,
                2,
            ),
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _policy_score(
        self,
        item: QuestionBankItem,
        policy: InterviewPolicy,
    ) -> float:

        score = 0.0

        if item.area.value in policy.preferred_areas:
            score += 1.0

        if policy.prioritize_architecture and item.area.value == "technical_case_study":
            score += 0.5

        if policy.prioritize_scalability:

            lower = item.text.lower()

            if any(
                k in lower
                for k in [
                    "scaling",
                    "distributed",
                    "replication",
                    "sharding",
                    "consistency",
                ]
            ):
                score += 0.5

        if policy.prioritize_production_experience:

            lower = item.text.lower()

            if any(
                k in lower
                for k in [
                    "production",
                    "deployment",
                    "pipeline",
                    "performance",
                    "monitoring",
                ]
            ):
                score += 0.5

        return score

    def _assign_stage(
        self,
        difficulty: int,
    ) -> InterviewStage:

        if difficulty <= 2:
            return InterviewStage.WARMUP

        if difficulty <= 4:
            return InterviewStage.CORE

        return InterviewStage.ADVANCED

    def _build_reason(
        self,
        stage: InterviewStage,
    ) -> str:

        if stage == InterviewStage.WARMUP:
            return "warmup_progression"

        if stage == InterviewStage.CORE:
            return "core_depth_evaluation"

        return "advanced_signal_assessment"

    def _calculate_progression(
        self,
        questions: list[AssembledQuestion],
    ) -> float:

        difficulties = [q.item.difficulty for q in questions]

        if len(difficulties) < 2:
            return 1.0

        ordered_pairs = 0

        for idx in range(len(difficulties) - 1):

            if difficulties[idx] <= difficulties[idx + 1]:
                ordered_pairs += 1

        return ordered_pairs / (len(difficulties) - 1)
