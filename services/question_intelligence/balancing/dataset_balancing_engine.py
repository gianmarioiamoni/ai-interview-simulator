# services/question_intelligence/balancing/dataset_balancing_engine.py

from collections import Counter

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.balancing.balancing_issue import (
    BalancingIssue,
)

from services.question_intelligence.balancing.balancing_report import (
    BalancingReport,
)


class DatasetBalancingEngine:

    MIN_BUCKET_SIZE = 3

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        items: list[QuestionBankItem],
    ) -> BalancingReport:

        issues: list[BalancingIssue] = []

        issues.extend(
            self._analyze_roles(
                items,
            )
        )

        issues.extend(
            self._analyze_levels(
                items,
            )
        )

        issues.extend(
            self._analyze_areas(
                items,
            )
        )

        return BalancingReport(
            total_issues=len(issues),
            issues=issues,
        )

    # =====================================================
    # ROLES
    # =====================================================

    def _analyze_roles(
        self,
        items: list[QuestionBankItem],
    ) -> list[BalancingIssue]:

        counter = Counter(item.role.type.value for item in items)

        return self._build_issues(
            dimension="role",
            counter=counter,
        )

    # =====================================================
    # LEVELS
    # =====================================================

    def _analyze_levels(
        self,
        items: list[QuestionBankItem],
    ) -> list[BalancingIssue]:

        counter = Counter(item.level.value for item in items)

        return self._build_issues(
            dimension="level",
            counter=counter,
        )

    # =====================================================
    # AREAS
    # =====================================================

    def _analyze_areas(
        self,
        items: list[QuestionBankItem],
    ) -> list[BalancingIssue]:

        counter = Counter(item.area.value for item in items)

        return self._build_issues(
            dimension="area",
            counter=counter,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _build_issues(
        self,
        dimension: str,
        counter: Counter,
    ) -> list[BalancingIssue]:

        issues: list[BalancingIssue] = []

        for value, count in counter.items():

            if count >= self.MIN_BUCKET_SIZE:
                continue

            severity = "high" if count == 1 else "medium"

            issues.append(
                BalancingIssue(
                    dimension=dimension,
                    value=value,
                    count=count,
                    severity=severity,
                    recommendation=(
                        f"Add more " f"{dimension} " f"questions for " f"{value}"
                    ),
                )
            )

        return issues
