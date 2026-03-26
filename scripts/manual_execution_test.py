from app.graph.nodes.execution_node import ExecutionNode
from services.execution_engine import ExecutionEngine

from tests.factories.interview_state_factory import build_interview_state


def main():
    engine = ExecutionEngine()
    node = ExecutionNode(engine)

    state = build_interview_state()

    new_state = node(state)

    result = new_state.get_result_for_question("q1")

    print("QUESTION:", state.current_question)
    print("ANSWER:", state.last_answer) 

    print("EXEC RESULT:", result)
    print("EXEC QUESTION ID:", result.execution.question_id) 

    if result and result.execution:
        print("SUCCESS:", result.execution.success)
    else:
        print("NO EXECUTION RESULT")


if __name__ == "__main__":
    main()
