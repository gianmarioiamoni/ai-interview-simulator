# app/ui/dto/builders/token_calculator.py


class TokenCalculator:

    def calculate(self, state) -> int:

        return sum(
            getattr(r.evaluation, "tokens_used", 0)
            for r in state.results_by_question.values()
            if r.evaluation
        )
