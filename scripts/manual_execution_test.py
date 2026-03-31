# scripts/manual_execution_test.py

from app.graph.interview_graph import build_interview_graph
from tests.factories.interview_state_factory import build_interview_state
from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType


def unwrap_state(graph_result):

    if isinstance(graph_result, dict):
        return InterviewState.model_validate(graph_result)

    return graph_result


def print_step(state: InterviewState):

    question = state.current_question
    result = state.get_result_for_question(question.id)

    print("\n==============================")
    print(f"QUESTION ID: {question.id}")
    print("PROMPT:", question.prompt)

    print("\n--- ANSWER ---")
    print(state.last_answer)

    print("\n--- EXECUTION ---")
    print(result.execution)

    print("\n--- EVALUATION ---")
    print(result.evaluation)

    print("\n--- HINT ---")
    print(result.ai_hint)

    print("\n--- FEEDBACK QUALITY ---")
    bundle = getattr(state, "last_feedback_bundle", None)
    if bundle:
        print(bundle.overall_quality)

    print("==============================\n")


def print_final_report(state: InterviewState):

    print("\n########################################")
    print("FINAL REPORT")
    print("########################################\n")

    print("FINAL FEEDBACK:\n")
    print(state.final_feedback)

    print("\n--- REPORT OUTPUT ---")
    print(state.report_output)

    print("\n--- INTERVIEW EVALUATION ---")
    eval = state.interview_evaluation

    print("Overall Score:", eval.overall_score)
    print("Hiring Probability:", eval.hiring_probability)
    print("Percentile:", eval.percentile_rank)

    print("\nDimensions:")
    for d in eval.performance_dimensions:
        print(f"- {d.name}: {d.score}")

    print("\nImprovements:")
    for i in eval.improvement_suggestions:
        print(f"- {i}")

    print("\n########################################\n")


def main():

    # ---------------------------------------------------------
    # Build graph with real dependencies (or mock if vuoi)
    # ---------------------------------------------------------

    from infrastructure.llm.llm_adapter import DefaultLLMAdapter
    from services.ai_hint_engine.ai_hint_service import AIHintService

    llm = DefaultLLMAdapter()
    hint_service = AIHintService(llm)

    graph = build_interview_graph(
        llm=llm,
        hint_service=hint_service,
    ).invoke(state)

    # ---------------------------------------------------------
    # Initial state
    # ---------------------------------------------------------

    state = build_interview_state()

    print("\n🚀 START INTERVIEW\n")

    step = 1

    # ---------------------------------------------------------
    # Loop until completion
    # ---------------------------------------------------------

    while True:

        print(f"\n=== STEP {step} ===")

        state.last_action = ActionType.NEXT

        graph_result = graph.invoke(state)
        state = unwrap_state(graph_result)

        print_step(state)

        if state.is_completed:
            break

        step += 1

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------

    print_final_report(state)


if __name__ == "__main__":
    main()
