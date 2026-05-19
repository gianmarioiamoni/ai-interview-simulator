# services/interview_selection/interview_question_selector.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.interview_selection.selected_question import (
    SelectedQuestion,
)

from services.interview_selection.interview_selection_result import (
    InterviewSelectionResult,
)


class InterviewQuestionSelector:

    # =====================================================
    # PUBLIC
    # =====================================================

    def select(
        self,
        candidates: list[QuestionBankItem],
        max_questions: int = 5,
    ) -> InterviewSelectionResult:

        selected: list[SelectedQuestion] = []

        used_areas: set[str] = set()

        area_buckets = self._group_by_area(
            candidates,
        )

        # -------------------------------------------------
        # FIRST PASS
        # maximize coverage
        # -------------------------------------------------

        for area, questions in area_buckets.items():

            if len(selected) >= max_questions:
                break

            best = max(
                questions,
                key=lambda q: (q.difficulty),
            )

            selected.append(
                SelectedQuestion(
                    item=best,
                    selection_score=1.0,
                    selection_reason=("coverage_maximization"),
                )
            )

            used_areas.add(area)

        # -------------------------------------------------
        # SECOND PASS
        # fill remaining slots
        # -------------------------------------------------

        remaining = [q for q in candidates if q.id not in {s.item.id for s in selected}]

        remaining.sort(
            key=lambda q: (q.difficulty),
            reverse=True,
        )

        for item in remaining:

            if len(selected) >= max_questions:
                break

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=0.7,
                    selection_reason=("difficulty_prioritization"),
                )
            )

        coverage_score = len({s.item.area.value for s in selected}) / max(
            len(area_buckets),
            1,
        )

        average_difficulty = sum(s.item.difficulty for s in selected) / max(
            len(selected),
            1,
        )

        return InterviewSelectionResult(
            selected_questions=(selected),
            total_questions=len(selected),
            coverage_score=round(
                coverage_score,
                2,
            ),
            average_difficulty=round(
                average_difficulty,
                2,
            ),
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _group_by_area(
        self,
        items: list[QuestionBankItem],
    ):

        buckets = defaultdict(list)

        for item in items:

            buckets[item.area.value].append(item)

        return buckets
