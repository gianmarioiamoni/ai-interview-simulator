# app/ui/presenters/feedback/blocks/written_block.py


class WrittenBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(evaluation and not execution)

    def build(self, state, result, evaluation, execution, analysis) -> str:

        return "\n".join(
            [
                f"## Score: {evaluation.score:.1f}/100\n",
                "### Feedback",
                evaluation.feedback + "\n",
            ]
        )
