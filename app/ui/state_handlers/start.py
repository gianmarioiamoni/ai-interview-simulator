# app/ui/state_handlers/start.py

from typing import Generator

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.question.question import QuestionType
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ai.test_generation.ai_test_generator import AITestGenerator

from app.runtime.interview_runtime import run_interview_graph
from app.runtime.interview_runtime import get_runtime_llm

from app.settings.constants import QUESTIONS_PER_AREA

from app.ui.ui_response import UIResponse


def start_interview(
    role: str,
    interview_type: str,
    company: str,
    language: str,
) -> Generator[UIResponse, None, None]:

    # -----------------------------------------
    # INITIAL STATE
    # -----------------------------------------
    state = InterviewState.empty()

    state.awaiting_user_input = False
    yield state

    # -----------------------------------------
    # GENERATE QUESTIONS
    # -----------------------------------------
    questions = ...

    yield state

    # -----------------------------------------
    # BUILD FINAL STATE
    # -----------------------------------------
    state = InterviewState.create_initial(...)

    yield state

    # -----------------------------------------
    # GRAPH
    # -----------------------------------------
    state = run_interview_graph(state)

    state.awaiting_user_input = True

    yield state

    # -----------------------------------------------------
    # STEP 4 — GENERATE TESTS
    # -----------------------------------------------------

    yield UIResponse(
        state=None,
        loader_visible=True,
        loader_value="🧪 Preparing test cases...",
    )

    enriched_questions = []

    for q in questions:
        if q.type == QuestionType.CODING:

            if not q.coding_spec:
                raise ValueError("Coding question missing CodingSpec")

            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    # -----------------------------------------------------
    # STEP 5 — BUILD STATE
    # -----------------------------------------------------

    yield UIResponse(
        state=None,
        loader_visible=True,
        loader_value="⚙️ Building interview state...",
    )

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    # -----------------------------------------------------
    # STEP 6 — GRAPH EXECUTION
    # -----------------------------------------------------

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🚀 Running interview engine...",
    )

    new_state = run_interview_graph(state)

    # -----------------------------------------------------
    # FIX STATE (CRITICO)
    # -----------------------------------------------------

    new_state.awaiting_user_input = True

    # -----------------------------------------------------
    # STEP 7 — FINAL UI
    # -----------------------------------------------------

    response = build_ui_response_from_state(new_state)

    yield response
