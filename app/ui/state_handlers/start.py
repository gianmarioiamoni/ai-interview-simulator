## app/ui/state_handlers/start.py

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

from app.runtime.interview_runtime import run_interview_graph, get_runtime_llm
from app.settings.constants import QUESTIONS_PER_AREA


def start_interview(role: str, interview_type: str, company: str, language: str):

    # -----------------------------------------------------
    # SAFE ENUM MAPPING
    # -----------------------------------------------------
    try:
        role_type = RoleType(role)
    except ValueError:
        raise ValueError(f"Invalid role selected: {role}")

    try:
        interview_type_enum = InterviewType[interview_type]
    except KeyError:
        raise ValueError(f"Invalid interview type: {interview_type}")

    level_enum = SeniorityLevel.MID  # TODO: rendere dinamico

    # -----------------------------------------------------
    # QUESTION GENERATION
    # -----------------------------------------------------
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
        if q.type == QuestionType.CODING:

            if not q.coding_spec:
                raise ValueError("Coding question missing CodingSpec")

            hidden_tests = test_generator.generate_tests(q, num_tests=3)
            q = q.model_copy(update={"hidden_tests": hidden_tests})

        enriched_questions.append(q)

    # -----------------------------------------------------
    # STATE INIT
    # -----------------------------------------------------
    state = InterviewState.create_initial(
        role_type=role_type,
        interview_type=interview_type_enum,
        company=company,
        language=language,
        questions=enriched_questions,
        interview_id="session-1",
    )

    # -----------------------------------------------------
    # GRAPH EXECUTION
    # -----------------------------------------------------
    new_state = run_interview_graph(state)

    print("\n=== START INTERVIEW DEBUG ===")
    print("current_question_id:", getattr(new_state.current_question, "id", None))
    print("allowed_actions:", new_state.allowed_actions)
    print("is_completed:", new_state.is_completed)
    print("================================\n")

    return build_ui_response_from_state(new_state)
