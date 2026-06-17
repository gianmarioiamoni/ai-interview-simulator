# services/question_intelligence/retrieval_query_builder.py

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from services.question_intelligence.retrieval.retrieval_area_hints import (
    AREA_HINTS,
)

from services.question_intelligence.retrieval.retrieval_role_hints import (
    ROLE_HINTS,
)

from services.question_intelligence.retrieval.retrieval_level_hints import (
    LEVEL_HINTS,
)

_SENIORITY_INTENT = {
    SeniorityLevel.JUNIOR: (
        "entry-level fundamentals, basic query writing, and debugging SQL"
    ),
    SeniorityLevel.MID: (
        "production SQL scenarios, optimization trade-offs, and real workloads"
    ),
    SeniorityLevel.SENIOR: (
        "advanced database design, scaling, distributed data, and architecture"
    ),
}

_ROLE_INTENT = {
    RoleType.BACKEND_ENGINEER: "backend API and data persistence",
    RoleType.FRONTEND_ENGINEER: "client-facing data access patterns",
    RoleType.FULLSTACK_ENGINEER: "full-stack data modeling and queries",
    RoleType.DEVOPS_ENGINEER: "database operations, reliability, and scaling",
    RoleType.DATA_ENGINEER: "ETL pipelines, warehousing, and analytics SQL",
    RoleType.ML_ENGINEER: "feature stores, model-serving data, and batch SQL",
    RoleType.QA_ENGINEER: "data validation, test databases, and integrity checks",
    RoleType.OTHER: "general software engineering database usage",
}


class RetrievalQueryBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        theme_anchor: str | None = None,
        memory: InterviewRetrievalMemory | None = None,
    ) -> str:

        area_hints = AREA_HINTS.get(area, [])
        role_hints = ROLE_HINTS.get(role, [])
        level_hints = LEVEL_HINTS.get(level, [])

        offset = self._rotation_offset(
            role=role,
            level=level,
            area=area,
            memory=memory,
        )

        area_topics = self._rotate_hints(
            hints=area_hints,
            count=min(3, len(area_hints)),
            offset=offset,
        )
        role_topics = self._rotate_hints(
            hints=role_hints,
            count=min(3, len(role_hints)),
            offset=offset + 7,
        )
        level_topics = self._rotate_hints(
            hints=level_hints,
            count=min(2, len(level_hints)),
            offset=offset + 13,
        )

        adaptive_topics: list[str] = []
        if memory and memory.weak_domains:
            adaptive_topics.extend(d.value for d in memory.weak_domains[:2])
        if memory and memory.strong_domains:
            adaptive_topics.extend(
                [f"not {domain.value}" for domain in memory.strong_domains[:1]],
            )

        all_topics = area_topics + role_topics + level_topics + adaptive_topics
        topics_text = ", ".join(dict.fromkeys(all_topics))

        seniority_intent = _SENIORITY_INTENT.get(
            level,
            "practical engineering interview scenarios",
        )
        role_intent = _ROLE_INTENT.get(
            role,
            f"{role.value.replace('_', ' ')} context",
        )

        theme_text = ""
        if theme_anchor:
            theme_text = theme_anchor.replace("_", " ")

        avoid_text = ""
        if memory and memory.session_used_topics:
            avoid_text = ", ".join(memory.session_used_topics[-3:])

        template_index = offset % 5

        if template_index == 0:
            lead = area_topics[0] if area_topics else area.value
            return (
                f"{lead} SQL interview question. "
                f"{seniority_intent}. "
                f"{role_intent}. "
                f"Topics: {topics_text}."
                + (f" Theme: {theme_text}." if theme_text else "")
                + (f" Avoid: {avoid_text}." if avoid_text else "")
            )

        if template_index == 1:
            return (
                f"{role_intent} — {seniority_intent}. "
                f"Cover {topics_text}."
                + (f" Scenario theme: {theme_text}." if theme_text else "")
            )

        if template_index == 2:
            return (
                f"Database interview for {level.value} {role.value.replace('_', ' ')}: "
                f"{topics_text}. "
                f"Emphasis on {seniority_intent}."
                + (f" Anchor: {theme_text}." if theme_text else "")
            )

        if template_index == 3:
            primary = ", ".join(all_topics[:3]) if all_topics else "sql"
            secondary = ", ".join(all_topics[3:])
            return (
                f"Find questions about {primary}"
                + (f" with {secondary}" if secondary else "")
                + f". {role_intent}. {seniority_intent}."
                + (f" Related to {theme_text}." if theme_text else "")
            )

        return (
            f"{seniority_intent} — {topics_text} — {role_intent}."
            + (f" Interview theme {theme_text}." if theme_text else "")
            + (f" Skip recently used {avoid_text}." if avoid_text else "")
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _rotation_offset(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        memory: InterviewRetrievalMemory | None,
    ) -> int:

        base = hash((role.value, level.value, area.value)) & 0xFFFF

        if memory is None:
            return base

        return (
            base
            + len(memory.asked_question_ids) * 3
            + len(memory.session_used_topics) * 2
            + len(memory.covered_domains)
            + len(memory.weak_domains) * 5
        )

    def _rotate_hints(
        self,
        hints: list[str],
        count: int,
        offset: int,
    ) -> list[str]:

        if not hints or count <= 0:
            return []

        start = offset % len(hints)
        picked: list[str] = []

        for index in range(min(count, len(hints))):
            picked.append(hints[(start + index) % len(hints)])

        return picked
