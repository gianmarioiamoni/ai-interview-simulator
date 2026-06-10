# services/interview_orchestration/orchestration_intent_builder.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from domain.contracts.retrieval.retrieval_planning_intent import RetrievalPlanningIntent


class OrchestrationIntentBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
    ) -> RetrievalPlanningIntent:

        focus_areas = self._build_focus_areas(role)

        required_tags = self._build_required_tags(role)

        query_text = self._build_query_text(
            role=role,
            level=level,
        )

        return RetrievalPlanningIntent(
            focus_areas=(focus_areas),
            required_tags=(required_tags),
            target_level=(level.value),
            query_text=(query_text),
            max_candidates=15,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _build_focus_areas(
        self,
        role: RoleType,
    ) -> list[str]:

        mapping = {
            RoleType.BACKEND_ENGINEER: [
                "distributed_systems",
                "backend",
                "database",
            ],
            RoleType.DEVOPS_ENGINEER: [
                "devops",
                "distributed_systems",
            ],
            RoleType.DATA_ENGINEER: [
                "data_engineering",
                "database",
            ],
        }

        return mapping.get(
            role,
            ["backend"],
        )

    def _build_required_tags(
        self,
        role: RoleType,
    ) -> list[str]:

        mapping = {
            RoleType.BACKEND_ENGINEER: [
                "distributed_systems",
            ],
            RoleType.DEVOPS_ENGINEER: [
                "devops",
            ],
            RoleType.DATA_ENGINEER: [
                "data_engineering",
            ],
        }

        return mapping.get(
            role,
            [],
        )

    def _build_query_text(
        self,
        role: RoleType,
        level: SeniorityLevel,
    ) -> str:

        role_queries = {
            RoleType.BACKEND_ENGINEER: (
                "distributed systems " "backend scalability " "consistency architecture"
            ),
            RoleType.DEVOPS_ENGINEER: (
                "kubernetes deployment " "ci cd observability " "infrastructure"
            ),
            RoleType.DATA_ENGINEER: (
                "data pipelines " "stream processing " "distributed data systems"
            ),
        }

        base_query = role_queries.get(
            role,
            "software engineering",
        )

        return f"{base_query} " f"{level.value}"
