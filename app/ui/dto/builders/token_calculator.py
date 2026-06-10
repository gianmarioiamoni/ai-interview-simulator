# app/ui/dto/builders/token_calculator.py


class TokenCalculator:

    def calculate(self, state) -> int:

        interview_metrics = getattr(state, "interview_metrics", None)
        if interview_metrics is not None:
            return interview_metrics.total_tokens

        return sum(
            getattr(r.evaluation, "tokens_used", 0)
            for r in state.results_by_question.values()
            if r.evaluation
        )

    def calculate_total_cost_usd(self, state) -> float | None:
        interview_cost_metrics = getattr(state, "interview_cost_metrics", None)
        if interview_cost_metrics is not None:
            return interview_cost_metrics.total_cost_usd
        return None

    def calculate_cost_per_question_usd(self, state) -> float | None:
        interview_cost_metrics = getattr(state, "interview_cost_metrics", None)
        if interview_cost_metrics is not None:
            return interview_cost_metrics.cost_per_question_usd
        return None
