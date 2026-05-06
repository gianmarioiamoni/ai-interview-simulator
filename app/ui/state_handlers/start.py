# app/ui/state_handlers/start.py

from typing import Generator

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

from app.ai.test_generation.ai_test_generator import AITestGenerator
from app.settings.constants import QUESTIONS_PER_AREA
from app.runtime.interview_runtime import run_interview_graph, get_runtime_llm

from domain.contracts.interview_state import InterviewState

from app.ui.ui_response import UIResponse
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def start_interview(role, interview_type, company, language) -> Generator:

    # -----------------------------------------------------
    # STEP 0 — PLACEHOLDER STATE (per attivare loader subito)
    # -----------------------------------------------------

    state = InterviewState.create_empty()

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🧠 Generating interview structure...",
    ).to_gradio_outputs()

    # -----------------------------------------------------
    # STEP 1 — ENUM RESOLUTION
    # -----------------------------------------------------

    role_type = RoleType(role)
    interview_type_enum = InterviewType[interview_type]
    level_enum = SeniorityLevel.MID

    # -----------------------------------------------------
    # STEP 2 — INIT SERVICES
    # -----------------------------------------------------

    llm = get_runtime_llm()

    question_intelligence = QuestionIntelligenceProvider(llm)
    test_generator = AITestGenerator(llm)

    # -----------------------------------------------------
    # STEP 3 — GENERATE QUESTIONS
    # -----------------------------------------------------

    questions = question_intelligence.generate(
        role=role_type,
        level=level_enum,
        interview_type=interview_type_enum,
        areas=interview_type_enum.get_areas(),
        questions_per_area=QUESTIONS_PER_AREA,
    )

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="📚 Creating questions...",
    ).to_gradio_outputs()

    # -----------------------------------------------------
    # STEP 4 — GENERATE TESTS
    # -----------------------------------------------------

    enriched_questions = []

    for q in questions:
        if q.type.name == "CODING":
            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🧪 Preparing test cases...",
    ).to_gradio_outputs()

    # -----------------------------------------------------
    # STEP 5 — BUILD FINAL STATE
    # -----------------------------------------------------

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="⚙️ Finalizing interview...",
    ).to_gradio_outputs()

    # -----------------------------------------------------
    # STEP 6 — GRAPH EXECUTION
    # -----------------------------------------------------

    state = run_interview_graph(state)
    state.awaiting_user_input = True

    # -----------------------------------------------------
    # FINAL UI
    # -----------------------------------------------------

    yield build_ui_response_from_state(state).to_gradio_outputs()
