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
from services.interview_length.interview_length_planner import (
    compute_questions_per_area as _compute_questions_per_area,
    expand_planned_areas as _expand_planned_areas,
)

from app.ai.test_generation.ai_test_generator import AITestGenerator
from app.settings.constants import (
    QUESTIONS_PER_AREA,
    USE_BATCH_QUESTION_GENERATION,
    DEFAULT_INTERVIEW_LENGTH,
    TECHNICAL_AREA_WEIGHTS,
)
from app.runtime.interview_runtime import (
    run_interview_graph,
    get_runtime_llm,
    get_runtime_metrics_collector,
)
from app.graph.nodes.navigation_node import configure_navigation_node

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.business_context import BusinessContext
from services.question_intelligence.coding_domain_profile_registry import (
    CodingDomainProfileRegistry,
)

from infrastructure.config.settings import settings
from services.humanizer.selector.follow_up_selector import FollowUpSelector
from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.constants.loader_steps import LoaderStep
from app.ui.mappers.loader_mapper import map_loader_progress
from app.ui.adapters.ui_output_adapter import UIOutputAdapter


def start_interview(
    role,
    role_custom_name,
    interview_type,
    seniority,
    interview_length,
    company,
    language,
    job_description=None,
    company_description=None,
) -> Generator:
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
    role_custom = role_custom_name.strip() if role_custom_name and role_custom_name.strip() else None
    interview_type_enum = InterviewType[interview_type]
    level_enum = SeniorityLevel(seniority) if seniority else SeniorityLevel.MID
    resolved_length = int(interview_length) if interview_length else DEFAULT_INTERVIEW_LENGTH

    get_runtime_metrics_collector().start_session()
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

    raw_cd = company_description.strip() if company_description and company_description.strip() else None
    resolved_business_context = BusinessContext.from_company_description(raw_cd)
    resolved_domain_profile = CodingDomainProfileRegistry.get(resolved_business_context)

    areas = interview_type_enum.get_areas()
    area_question_counts = _compute_questions_per_area(
        interview_length=resolved_length,
        areas=areas,
        weights=TECHNICAL_AREA_WEIGHTS if interview_type_enum.name == "TECHNICAL" else None,
    )

    if USE_BATCH_QUESTION_GENERATION:
        questions = question_intelligence.generate(
            role=role_type,
            level=level_enum,
            interview_type=interview_type_enum,
            areas=areas,
            questions_per_area=QUESTIONS_PER_AREA,
        )
    else:

        def _enrich_question(question):
            if question.type.name == "CODING":
                hidden_tests = test_generator.generate_tests(
                    question, num_tests=3, domain_profile=resolved_domain_profile
                )
                return question.model_copy(update={"hidden_tests": hidden_tests})
            return question

        configure_navigation_node(
            lazy_service=question_intelligence.lazy_adaptive_service,
            question_enricher=_enrich_question,
            seniority_level=level_enum,
        )

        jd_for_generation = (
            job_description.strip()[:settings.job_description_max_chars]
            if job_description and job_description.strip()
            else None
        )

        cd_for_generation = raw_cd[:settings.company_description_max_chars] if raw_cd else None

        questions, retrieval_memory, planned_areas = (
            question_intelligence.generate_first_question(
                role=role_type,
                level=level_enum,
                interview_type=interview_type_enum,
                job_description=jd_for_generation,
                company_description=cd_for_generation,
                business_context=resolved_business_context,
            )
        )

        planned_areas = _expand_planned_areas(area_question_counts, areas)

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
            hidden_tests = test_generator.generate_tests(
                q, num_tests=3, domain_profile=resolved_domain_profile
            )
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

    context_profile = InterviewContextProfile(
        job_description=job_description.strip() if job_description and job_description.strip() else None,
        company_description=raw_cd,
        business_context=resolved_business_context,
    )

    state = InterviewState.create_initial(
        role_type=role_type,
        role_custom_name=role_custom,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
        seniority_level=level_enum.value,
        interview_length=resolved_length,
        context_profile=context_profile,
        enable_humanizer=settings.humanizer_enabled,
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
    # FOLLOW-UP SELECTOR — populate eligible indices once
    # -----------------------------------------------------

    if settings.humanizer_follow_up_enabled:
        eligible_indices = FollowUpSelector().select(
            total_questions=len(enriched_questions),
            planned_areas=planned_areas,
            settings=settings,
        )
        state = state.model_copy(
            update={"follow_up_eligible_indices": eligible_indices}
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
