## services/interview_selection/interview_question_selector.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_selection.selected_question import SelectedQuestion
from services.interview_selection.interview_selection_result import InterviewSelectionResult
from services.planning.planner_selection_scoring_engine import PlannerSelectionScoringEngine


class InterviewQuestionSelector:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._scoring_engine = PlannerSelectionScoringEngine()
    # =====================================================
    # PUBLIC
    # =====================================================

    def select(
        self,
        candidates: list[QuestionBankItem],
        max_questions: int = 5,
    ) -> InterviewSelectionResult:

        selected: list[SelectedQuestion] = []

        area_buckets = self._group_by_area(
            candidates,
        )

        # -------------------------------------------------
        # FIRST PASS
        # maximize coverage
        # -------------------------------------------------

        for _, questions in area_buckets.items():

            if len(selected) >= max_questions:
                break

            best: QuestionBankItem | None = None

            best_score = -1.0

            current_selected = [s.item for s in selected]

            for question in questions:

                base_score = float(question.difficulty)

                adjusted_score = self._scoring_engine.score(
                    candidate=question,
                    selected_questions=current_selected,
                )

                print()

                print("[PLANNER]" " semantic balancing")

                print(f"question: " f"{question.text}")

                print(f"base_score: " f"{base_score}")

                print(f"adjusted_score: " f"{adjusted_score}")

                if adjusted_score > best_score:

                    best = question

                    best_score = adjusted_score

            if best is None:
                continue

            selected.append(
                SelectedQuestion(
                    item=best,
                    selection_score=(best_score),
                    selection_reason=("coverage_maximization"),
                )
            )

        # -------------------------------------------------
        # SECOND PASS
        # fill remaining slots
        # -------------------------------------------------

        selected_ids = {s.item.id for s in selected}

        remaining = [q for q in candidates if q.id not in selected_ids]

        current_selected = [s.item for s in selected]

        scored_remaining: list[
            tuple[
                QuestionBankItem,
                float,
            ]
        ] = []

        for item in remaining:

            base_score = float(item.difficulty)

            adjusted_score = self._scoring_engine.score(
                candidate=item,
                selected_questions=current_selected,
            )

            print()

            print("[PLANNER]" " semantic balancing")

            print(f"question: " f"{item.text}")

            print(f"base_score: " f"{base_score}")

            print(f"adjusted_score: " f"{adjusted_score}")

            scored_remaining.append(
                (
                    item,
                    adjusted_score,
                )
            )

        scored_remaining.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        for item, adjusted_score in scored_remaining:

            if len(selected) >= max_questions:
                break

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=(adjusted_score),
                    selection_reason=("semantic_balancing"),
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
    ) -> dict[str, list[QuestionBankItem]]:

        buckets = defaultdict(list)

        for item in items:

            buckets[item.area.value].append(item)

        return buckets
