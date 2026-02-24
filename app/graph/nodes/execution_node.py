# app/graph/nodes/execution_node.py

# Responsibility:
# Execute code
# Timeout
# Structured ExecutionResult

from domain.contracts.interview_state import InterviewState


def execution_node(state: InterviewState) -> InterviewState:
    # Only execute if question type requires it
    if not state.current_question:
        return state

    if state.current_question.type not in ["coding", "sql"]:
        return state

    # Call appropriate engine
    result = run_engine(question=state.current_question, answer=state.current_answer)

    state.execution_result = result

    return state
