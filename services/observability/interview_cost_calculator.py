# services/observability/interview_cost_calculator.py

from domain.contracts.interview.interview_cost_metrics import (
    InterviewCostMetrics,
    OperationCostMetrics,
)
from domain.contracts.interview.interview_metrics import InterviewMetrics
from infrastructure.llm.pricing.openai_pricing import calculate_token_cost_usd


class InterviewCostCalculator:

    def calculate(
        self,
        metrics: InterviewMetrics,
        *,
        question_count: int = 0,
        model_name: str | None = None,
    ) -> InterviewCostMetrics:
        operations: list[OperationCostMetrics] = []

        for operation_metrics in metrics.operations:
            cost_usd = calculate_token_cost_usd(
                input_tokens=operation_metrics.input_tokens,
                output_tokens=operation_metrics.output_tokens,
                model_name=model_name,
            )
            operations.append(
                OperationCostMetrics(
                    operation=operation_metrics.operation,
                    input_tokens=operation_metrics.input_tokens,
                    output_tokens=operation_metrics.output_tokens,
                    cost_usd=cost_usd,
                )
            )

        total_cost_usd = calculate_token_cost_usd(
            input_tokens=metrics.total_input_tokens,
            output_tokens=metrics.total_output_tokens,
            model_name=model_name,
        )

        cost_per_question_usd = (
            round(total_cost_usd / question_count, 6) if question_count > 0 else 0.0
        )

        return InterviewCostMetrics(
            total_cost_usd=total_cost_usd,
            cost_per_question_usd=cost_per_question_usd,
            operations=operations,
        )
