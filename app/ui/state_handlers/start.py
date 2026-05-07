# app/ui/state_handlers/start.py

from typing import Generator
import time

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

from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.constants.loader_steps import LoaderStep
from app.ui.mappers.loader_mapper import map_loader_progress


def start_interview(role, interview_type, company, language) -> Generator:

    # -----------------------------------------------------
    # STEP 0 — EMPTY STATE + LOADER
    # -----------------------------------------------------

    state = InterviewState.create_empty()
    state.current_step = LoaderStep.GENERATING_STRUCTURE
    state.current_progress = map_loader_progress(state.current_step)

    yield build_ui_response_from_state(state).to_gradio_outputs()

    time.sleep(0.3)

    # -----------------------------------------------------
    # STEP 1 — ENUM
    # -----------------------------------------------------

    role_type = RoleType(role)
    interview_type_enum = InterviewType[interview_type]
    level_enum = SeniorityLevel.MID

    llm = get_runtime_llm()

    question_intelligence = QuestionIntelligenceProvider(llm)
    test_generator = AITestGenerator(llm)

    # -----------------------------------------------------
    # STEP 2 — QUESTIONS
    # -----------------------------------------------------

    state.current_step = LoaderStep.GENERATING_QUESTIONS
    state.current_progress = map_loader_progress(state.current_step)
    
    yield build_ui_response_from_state(state).to_gradio_outputs()
    time.sleep(0.2)

    questions = question_intelligence.generate(
        role=role_type,
        level=level_enum,
        interview_type=interview_type_enum,
        areas=interview_type_enum.get_areas(),
        questions_per_area=QUESTIONS_PER_AREA,
    )

    # -----------------------------------------------------
    # STEP 3 — TESTS
    # -----------------------------------------------------

    state.current_step = LoaderStep.GENERATING_TESTS
    state.current_progress = map_loader_progress(state.current_step)
    
    yield build_ui_response_from_state(state).to_gradio_outputs()
    time.sleep(0.2)

    enriched_questions = []

    for q in questions:
        if q.type.name == "CODING":
            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    # -----------------------------------------------------
    # STEP 4 — BUILD STATE
    # -----------------------------------------------------

    state.current_step = LoaderStep.FINALIZING
    state.current_progress = map_loader_progress(state.current_step)
    
    yield build_ui_response_from_state(state).to_gradio_outputs()
    time.sleep(0.2)

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    # -----------------------------------------------------
    # STEP 5 — GRAPH
    # -----------------------------------------------------

    state = run_interview_graph(state)
    state.awaiting_user_input = True
    state.current_step = None  

    # -----------------------------------------------------
    # FINAL UI
    # -----------------------------------------------------

    yield build_ui_response_from_state(state).to_gradio_outputs()
