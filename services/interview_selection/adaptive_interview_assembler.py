# services/interview_selection/adaptive_interview_assembler.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.interview_selection.assembled_question import (
    AssembledQuestion,
)

from services.interview_selection.adaptive_interview_result import (
    AdaptiveInterviewResult,
)

from services.interview_selection.interview_stage import (
    InterviewStage,
)


class AdaptiveInterviewAssembler:

    MAX_PER_AREA = 2

    # =====================================================
    # PUBLIC
    # =====================================================

    def assemble(
        self,
        items: list[QuestionBankItem],
        max_questions: int = 5,
    ) -> AdaptiveInterviewResult:

        sorted_items = sorted(
            items,
            key=lambda q: (q.difficulty),
        )

        selected: list[AssembledQuestion] = []

        area_counts = defaultdict(int)

        for item in sorted_items:

            if len(selected) >= max_questions:
                break

            area = item.area.value

            if area_counts[area] >= self.MAX_PER_AREA:
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
                )
            )

            area_counts[area] += 1

        coverage_score = len({q.item.area.value for q in selected}) / max(
            len({i.area.value for i in items}),
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
