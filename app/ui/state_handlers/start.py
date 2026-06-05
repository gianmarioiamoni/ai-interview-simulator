# app/ui/state_handlers/start.py

from typing import Generator
import time

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.shared.action_type import ActionType

from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

from app.ai.test_generation.ai_test_generator import AITestGenerator
from app.settings.constants import QUESTIONS_PER_AREA, USE_BATCH_QUESTION_GENERATION
from app.runtime.interview_runtime import run_interview_graph, get_runtime_llm
from app.graph.nodes.navigation_node import configure_navigation_node

from domain.contracts.interview_state import InterviewState

from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.constants.loader_steps import LoaderStep
from app.ui.mappers.loader_mapper import map_loader_progress
from app.ui.adapters.ui_output_adapter import UIOutputAdapter


def start_interview(role, interview_type, company, language) -> Generator:
    def _smooth_progress(current, target):
        return min(current + 3, target)

    # -----------------------------------------------------
    # STEP 0 — EMPTY STATE + LOADER
    # -----------------------------------------------------

    state = InterviewState.create_empty()
    state.current_step = LoaderStep.GENERATING_STRUCTURE
    state.current_progress = map_loader_progress(state.current_step)

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
    state.current_progress = _smooth_progress(state.current_progress, map_loader_progress(LoaderStep.GENERATING_QUESTIONS))

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

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
    state.current_progress = _smooth_progress(state.current_progress, map_loader_progress(LoaderStep.GENERATING_TESTS))
    time.sleep(0.2)

    retrieval_memory = None
    planned_areas: list[str] = []
    adaptive_enabled = not USE_BATCH_QUESTION_GENERATION

    if USE_BATCH_QUESTION_GENERATION:
        questions = question_intelligence.generate(
            role=role_type,
            level=level_enum,
            interview_type=interview_type_enum,
            areas=interview_type_enum.get_areas(),
            questions_per_area=QUESTIONS_PER_AREA,
        )
    else:

        def _enrich_question(question):
            if question.type.name == "CODING":
                hidden_tests = test_generator.generate_tests(question, num_tests=3)
                return question.model_copy(update={"hidden_tests": hidden_tests})
            return question

        configure_navigation_node(
            lazy_service=question_intelligence.lazy_adaptive_service,
            question_enricher=_enrich_question,
        )

        questions, retrieval_memory, planned_areas = (
            question_intelligence.generate_first_question(
                role=role_type,
                level=level_enum,
                interview_type=interview_type_enum,
            )
        )

    # -----------------------------------------------------
    # STEP 3 — TESTS
    # -----------------------------------------------------

    state.current_step = LoaderStep.GENERATING_TESTS
    state.current_progress = map_loader_progress(state.current_step)

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
    state.current_progress = _smooth_progress(state.current_progress, map_loader_progress(LoaderStep.FINALIZING))
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

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
    state.current_progress = _smooth_progress(state.current_progress, 100)
    time.sleep(0.2)

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    if adaptive_enabled and retrieval_memory is not None:
        state = state.model_copy(
            update={
                "retrieval_memory": retrieval_memory,
                "planned_areas": planned_areas,
                "adaptive_interview_enabled": True,
            }
        )

    # -----------------------------------------------------
    # STEP 5 — GRAPH
    # -----------------------------------------------------

    state = run_interview_graph(state)
    
    state.awaiting_user_input = True
    state.is_processing = False  

    state.current_step = None
    state.current_progress = 0
    state.intent = ActionType.NONE  

    # -----------------------------------------------------
    # FINAL UI
    # -----------------------------------------------------

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
