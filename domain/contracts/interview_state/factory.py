from typing import Self
from uuid import uuid4

from domain.contracts.user.role import Role, RoleType
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.interview.interview_progress import InterviewProgress


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
    ) -> Self:

        return cls(
            interview_id=interview_id,
            role=Role(type=role_type),
            interview_type=interview_type,
            company=company.strip(),
            language=language,
            questions=questions,
            progress=InterviewProgress.SETUP,
        )

    # =========================================================
    # EMPTY STATE (CORRETTO PER ARCHITETTURA ATTUALE)
    # =========================================================

    @classmethod
    def create_empty(cls) -> Self:

        return cls(
            interview_id=f"session-{uuid4().hex[:8]}",
            # -------------------------------------------------
            # CORE DOMAIN (NO None → stato sempre valido)
            # -------------------------------------------------
            role=Role(type=RoleType.FULLSTACK_ENGINEER),
            interview_type=InterviewType.TECHNICAL,
            progress=InterviewProgress.SETUP,
            # -------------------------------------------------
            # BASIC INFO
            # -------------------------------------------------
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
            report_output=None,
            interview_evaluation=None,
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
            last_action=None,
        )
