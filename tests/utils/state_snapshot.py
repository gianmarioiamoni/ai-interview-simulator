# tests/utils/state_snapshot.py

from domain.contracts.interview_state import InterviewState


def serialize_state(state: InterviewState) -> dict:
    # Reduce state to deterministic snapshot for testing.

    return {
        "current_question_index": state.current_question_index,
        "is_completed": state.is_completed,
        "last_action": state.last_action,
        "results": {
            k: {
                "score": v.evaluation.score if v.evaluation else None,
                "has_execution": v.execution is not None,
                "has_hint": v.ai_hint is not None,
            }
            for k, v in state.results_by_question.items()
        },
        "report": state.report_output,
    }
