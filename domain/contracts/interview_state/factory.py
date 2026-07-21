from typing import Self
from uuid import uuid4, uuid5, NAMESPACE_URL

from domain.contracts.user.role import Role, RoleType
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.shared.action_type import ActionType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile


class InterviewStateFactoryMixin:

    @classmethod
    def create_initial(
        cls,
        role_type: RoleType,
        interview_type: InterviewType,
        company: str,
        language: str,
        questions: list[Question],
        interview_id: str,
        role_custom_name: str | None = None,
        seniority_level: str = "mid",
        interview_length: int = 20,
        context_profile: InterviewContextProfile | None = None,
        enable_humanizer: bool = True,
    ) -> Self:

        candidate_identity_id = str(uuid5(NAMESPACE_URL, f"candidate:{interview_id}"))

        return cls(
            interview_id=interview_id,
            candidate_identity_id=candidate_identity_id,
            role=Role(type=role_type, custom_name=role_custom_name),
            interview_type=interview_type,
            company=company.strip(),
            language=language,
            questions=questions,
            seniority_level=seniority_level,
            interview_length=interview_length,
            context_profile=context_profile or InterviewContextProfile(),
            enable_humanizer=enable_humanizer,
        )

    # =========================================================
    # EMPTY STATE (CORRETTO PER ARCHITETTURA ATTUALE)
    # =========================================================

    @classmethod
    def create_empty(cls) -> Self:

        _interview_id = f"session-{uuid4().hex[:8]}"
        return cls(
            interview_id=_interview_id,
            candidate_identity_id=str(uuid5(NAMESPACE_URL, f"candidate:{_interview_id}")),
            # -------------------------------------------------
            # CORE DOMAIN (NO None → stato sempre valido)
            # -------------------------------------------------
            role=Role(type=RoleType.FULLSTACK_ENGINEER),
            interview_type=InterviewType.TECHNICAL,
            # -------------------------------------------------
            # BASIC INFO
            # -------------------------------------------------
            # BASIC INFO
            company="",
            language="en",
            # -------------------------------------------------
            # DATA
            # -------------------------------------------------
            questions=[],
            asked_question_ids=[],
            answers=[],
            # -------------------------------------------------
            # RESULTS
            # -------------------------------------------------
            interview_metrics=None,
            interview_cost_metrics=None,
            results_by_question={},
            dimension_signals={},
            # -------------------------------------------------
            # FLOW
            # -------------------------------------------------
            current_question_index=0,
            is_completed=False,
            # -------------------------------------------------
            # RUNTIME
            # -------------------------------------------------
            chat_history=[],
            events=[],
            # -------------------------------------------------
            # CONTROL FLAGS
            # -------------------------------------------------
            awaiting_user_input=False,
            allowed_actions=[],
            last_feedback_bundle=None,
            intent=ActionType.NONE,
        )
