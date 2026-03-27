# app/application/services/report_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_evaluation import InterviewEvaluation


class ReportBuilder:

    @staticmethod
    def build(
        state: InterviewState,
        evaluation: InterviewEvaluation,
    ) -> InterviewState:

        final_feedback = ReportBuilder._build_feedback(evaluation)

        report_output = {
            "overall_score": evaluation.overall_score,
            "hiring_probability": evaluation.hiring_probability,
            "percentile": evaluation.percentile_rank,
            "confidence": evaluation.confidence.final,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "justification": d.justification,
                }
                for d in evaluation.performance_dimensions
            ],
            "improvements": evaluation.improvement_suggestions,
            "decision": "hire" if evaluation.hiring_probability >= 70 else "no_hire",
        }

        return state.model_copy(
            update={
                "final_feedback": final_feedback,
                "report_output": report_output,
                "interview_evaluation": evaluation,  # 🔥 IMPORTANTISSIMO
            }
        )

    @staticmethod
    def _build_feedback(evaluation: InterviewEvaluation) -> str:

        return (
            f"Overall Score: {evaluation.overall_score}\n"
            f"Hiring Probability: {evaluation.hiring_probability}%\n\n"
            f"{evaluation.executive_summary}\n\n"
            f"Top Improvements:\n"
            + "\n".join(f"- {i}" for i in evaluation.improvement_suggestions)
        )
