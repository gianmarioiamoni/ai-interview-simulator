# app/ui/state_handlers/start.py

from domain.contracts.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.question.question import QuestionType
from domain.contracts.interview_state import InterviewState

from app.ui.sample_data_loader import load_sample_questions
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.ai.test_generation.ai_test_generator import AITestGenerator

from app.runtime.interview_runtime import run_interview_graph

test_generator = AITestGenerator()


def start_interview(role: str, interview_type: str, company: str, language: str):

    role_type = RoleType[role.replace(" ", "_")]
    interview_type_enum = InterviewType[interview_type]

    questions = load_sample_questions(interview_type_enum.value)

    enriched_questions = []

    for q in questions:
        if q.type == QuestionType.CODING:

            if not q.coding_spec:
                raise ValueError("Coding question missing CodingSpec")
                
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

    # -----------------------------------------------------
    # GRAPH EXECUTION
    # -----------------------------------------------------
    
    new_state = run_interview_graph(state)
    response = build_ui_response_from_state(new_state)

    return response
