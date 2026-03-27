# app/services/report_builder.py

from domain.contracts.interview_state import InterviewState


class ReportBuilder:

    @staticmethod
    def build(state: InterviewState, aggregation: dict) -> InterviewState:

        final_feedback = ReportBuilder._build_feedback(aggregation)

        report_output = {
            "score": aggregation["score"],
            "decision": aggregation["decision"],
            "strengths": aggregation["strengths"],
            "weaknesses": aggregation["weaknesses"],
        }

        return state.model_copy(
            update={
                "final_feedback": final_feedback,
                "report_output": report_output,
            }
        )

    @staticmethod
    def _build_feedback(aggregation: dict) -> str:

        score = aggregation["score"]
        decision = aggregation["decision"]

        return (
            f"Final Score: {score}\n"
            f"Decision: {decision}\n\n"
            f"Strengths: {', '.join(aggregation['strengths'])}\n"
            f"Weaknesses: {', '.join(aggregation['weaknesses'])}"
        )
