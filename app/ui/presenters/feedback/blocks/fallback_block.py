# app/ui/presenters/feedback/blocks/fallback_block.py


class FallbackBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return True  # always last

    def build(self, state, result, evaluation, execution, analysis) -> str:

        return "Execution completed. No issues detected but no detailed feedback available.\n"
