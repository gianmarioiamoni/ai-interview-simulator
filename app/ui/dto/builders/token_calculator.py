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
