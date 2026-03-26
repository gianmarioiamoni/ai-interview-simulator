# scripts/manual_execution_test.py

# scripts/manual_execution_test.py

from app.graph.execution_graph import build_execution_graph
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.interview_state import InterviewState


def main():

    graph = build_execution_graph()

    state = build_interview_state()

    graph_result = graph.invoke(state)

    # ---------------------------------------------------------
    # Robust unwrap (LangGraph compatibility)
    # ---------------------------------------------------------
    if isinstance(graph_result, dict):
        new_state = InterviewState.model_validate(graph_result)
    else:
        new_state = graph_result

    question = new_state.current_question
    result = new_state.get_result_for_question(question.id)

    print("QUESTION:", question)
    print("ANSWER:", new_state.last_answer)

    print("\n=== EXECUTION ===")
    print(result.execution)

    print("\n=== EVALUATION ===")
    print(result.evaluation)

    print("\n=== HINT ===")
    print(result.ai_hint)


if __name__ == "__main__":
    main()
