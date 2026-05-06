# app/ui/state_handlers/start.py

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


def start_interview(role, interview_type, company, language):

    role_type = RoleType(role)
    interview_type_enum = InterviewType[interview_type]
    level_enum = SeniorityLevel.MID

    llm = get_runtime_llm()

    question_intelligence = QuestionIntelligenceProvider(llm)
    test_generator = AITestGenerator(llm)

    questions = question_intelligence.generate(
        role=role_type,
        level=level_enum,
        interview_type=interview_type_enum,
        areas=interview_type_enum.get_areas(),
        questions_per_area=QUESTIONS_PER_AREA,
    )

    enriched_questions = []

    for q in questions:
        if q.type.name == "CODING":
            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    state = run_interview_graph(state)
    state.awaiting_user_input = True

    return build_ui_response_from_state(state).to_gradio_outputs()
