# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from services.coding_engine.coding_executor import CodingExecutor
from services.sql_engine.sql_executor import SQLExecutor


def execution_node(state: InterviewState) -> InterviewState:

    # No answers yet
    if not state.answers:
        return state

    last_answer = state.answers[-1]

    question = next(
        (q for q in state.questions if q.id == last_answer.question_id),
        None,
    )

    if question is None:
        return state

    # ---------------------------------------------------------
    # CODING EXECUTION
    # ---------------------------------------------------------

    if question.type == QuestionType.CODING:

        executor = CodingExecutor()

        result = executor.execute(
            question_id=question.id,
            user_code=last_answer.content,
            function_name=question.function_name,
            test_cases=question.hidden_tests or [],
        )

        new_results = state.execution_results + [result]

        return state.model_copy(update={"execution_results": new_results})

    # ---------------------------------------------------------
    # SQL EXECUTION
    # ---------------------------------------------------------

    if question.type == QuestionType.DATABASE:

        executor = SQLExecutor()

        result = executor.execute(
            question,
            last_answer.content,
        )

        new_results = state.execution_results + [result]

        return state.model_copy(update={"execution_results": new_results})

    return state
