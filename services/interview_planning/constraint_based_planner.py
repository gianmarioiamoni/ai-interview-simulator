# services/interview_planning/constraint_based_planner.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.interview_planning.interview_constraints import (
    InterviewConstraints,
)

from services.interview_planning.planning_result import (
    PlanningResult,
)


class ConstraintBasedPlanner:

    # =====================================================
    # SCORING CONSTANTS
    # =====================================================

    DIFFICULTY_WEIGHT = 1.0

    AREA_DIVERSITY_BONUS = 2.0

    ROLE_DIVERSITY_BONUS = 1.0

    REDUNDANCY_PENALTY = 2.0

    AREA_SATURATION_BASE_PENALTY = 3.0

    # =====================================================
    # PUBLIC
    # =====================================================

    def plan(
        self,
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> PlanningResult:

        selected: list[QuestionBankItem] = []

        area_counts = defaultdict(int)

        # -------------------------------------------------
        # REQUIRED AREAS FIRST
        # -------------------------------------------------

        for area in constraints.required_areas:

            candidates = [item for item in items if (item.area.value == area)]

            if not candidates:
                continue

            best = max(
                candidates,
                key=lambda q: (q.difficulty),
            )

            selected.append(best)

            area_counts[area] += 1

        # -------------------------------------------------
        # FILL REMAINING
        # -------------------------------------------------

        remaining = sorted(
            [item for item in items if (item.id not in {q.id for q in selected})],
            key=lambda q: (q.difficulty),
            reverse=True,
        )

        for item in remaining:

            area = item.area.value

            if area in constraints.excluded_areas:
                continue

            if area_counts[area] >= constraints.max_questions_per_area:
                continue

            selected.append(item)

            area_counts[area] += 1

            if len(selected) >= constraints.minimum_total_questions:
                break

        average_difficulty = sum(q.difficulty for q in selected) / max(
            len(selected),
            1,
        )

        satisfied = []
        violated = []

        # -------------------------------------------------
        # REQUIRED AREAS
        # -------------------------------------------------

        selected_areas = {q.area.value for q in selected}

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

        return PlanningResult(
            selected_questions=selected_questions,
            satisfied_constraints=satisfied,
            violated_constraints=violated,
            average_difficulty=round(
                average_difficulty,
                2,
            ),
        )

    # =====================================================
    # FEASIBILITY
    # =====================================================

    def _fill_remaining_slots(
        self,
        selected: list[QuestionBankItem],
        available: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> list[QuestionBankItem]:

        # -------------------------------------------------
        # EARLY EXIT
        # -------------------------------------------------

        if len(selected) >= constraints.minimum_total_questions:

            return selected

        selected_ids = {item.id for item in selected}

        remaining = []

        for item in available:

            if item.id in selected_ids:
                continue

            remaining.append(item)

        # -------------------------------------------------
        # SORT BY DIFFICULTY
        # -------------------------------------------------
        print()
        print(
            "[PLANNER] "
            "Evaluating fallback candidates..."
        )

        remaining.sort(
            key=lambda candidate: (
                self._calculate_candidate_score(
                    candidate=candidate,
                    selected=selected,
                    constraints=constraints,
                )
            ),
            reverse=True,
        )

        # -------------------------------------------------
        # FILL
        # -------------------------------------------------

        for item in remaining:

            if len(selected) >= constraints.minimum_total_questions:

                break
            score = (
                self._calculate_candidate_score(
                    candidate=item,
                    selected=selected,
                    constraints=constraints,
                )
            )

            print()
            print(
                f"[PLANNER] "
                f"Selected fallback candidate: "
                f"{item.text}"
            )

            print(
                f"[PLANNER] "
                f"Score: {score}"
            )

            selected.append(item)

        return selected

    # =====================================================
    # SCORING
    # =====================================================

    def _calculate_candidate_score(
        self,
        candidate: QuestionBankItem,
        selected: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> float:

        score = 0.0

        # -------------------------------------------------
        # DIFFICULTY
        # -------------------------------------------------

        score += (
            candidate.difficulty
            * self.DIFFICULTY_WEIGHT
        )

        # -------------------------------------------------
        # AREA DIVERSITY
        # -------------------------------------------------

        selected_areas = {item.area.value for item in selected}

        if candidate.area.value not in selected_areas:

            score += self.AREA_DIVERSITY_BONUS

        # -------------------------------------------------
        # AREA SATURATION
        # -------------------------------------------------

        area_count = len(
            [item for item in selected if (item.area.value == candidate.area.value)]
        )

        overflow = max(
            0,
            (
                area_count
                + 1
                - constraints.max_questions_per_area
            ),
        )

        if overflow > 0:
            
            saturation_penalty = (
                overflow
                * self.AREA_SATURATION_BASE_PENALTY
            )

            score -= saturation_penalty
            
            print()

            print(
                f"[PLANNER] "
                f"Area saturation penalty "
                f"applied: "
                f"{candidate.area.value}"
            )

            print(
                f"[PLANNER] "
                f"Overflow: {overflow}"
            )

            print(
                f"[PLANNER] "
                f"Penalty: "
                f"{saturation_penalty}"
            )

        # -------------------------------------------------
        # ROLE DIVERSITY
        # -------------------------------------------------

        selected_roles = {item.role.type.value for item in selected}

        if candidate.role.type.value not in selected_roles:

            score += self.ROLE_DIVERSITY_BONUS

        # -------------------------------------------------
        # REDUNDANCY
        # -------------------------------------------------

        similar_questions = len(
            [item for item in selected if (item.text[:25] == candidate.text[:25])]
        )

        score -= (
            similar_questions
            * self.REDUNDANCY_PENALTY
        )

        return round(score, 2)
