# interface/cli/interview_cli_runner.py

# InterviewCLIRunner
#
# Responsibility:
# - orchestrate loop
# - connect adapter and graph
# - do not write critical fields
# - do not do business logic
# - persist and restore interview state


from pathlib import Path

from app.graph.interview_graph import build_interview_graph
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from interface.cli.input_adapter import CLIInputAdapter
from interface.cli.output_renderer import CLIOutputRenderer
from infrastructure.llm.llm_adapter import DefaultLLMAdapter


STATE_FILE = Path("data/interview_state.json")


class CLIRunner:
    # Coordinates CLI interaction with the LangGraph engine

    def __init__(self, llm=None) -> None:
        # Dependency Injection (critical for tests)
        if llm is None:
            llm = DefaultLLMAdapter()

        self.graph = build_interview_graph(llm)

        self.input_adapter = CLIInputAdapter()
        self.output_renderer = CLIOutputRenderer()

    # ----------------------------
    # Persistence helpers
    # ----------------------------

    def _save_state(self, state: InterviewState | dict) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(state, dict):
            state = InterviewState.model_validate(state)

        STATE_FILE.write_text(state.model_dump_json(indent=2))

    def _load_state(self) -> InterviewState | None:
        if not STATE_FILE.exists():
            return None
        return InterviewState.model_validate_json(STATE_FILE.read_text())

    def _cleanup_state(self) -> None:
        if STATE_FILE.exists():
            STATE_FILE.unlink()

    # ----------------------------
    # Main loop
    # ----------------------------

    def run(self, initial_state: InterviewState | None = None) -> InterviewState:

        # Resume if state file exists
        state = self._load_state() or initial_state

        if state is None:
            raise ValueError("Initial state required for new interview.")

        while state.progress != InterviewProgress.COMPLETED:

            # Execute graph until it blocks on awaiting_user_input
            result = self.graph.invoke(state)

            # LangGraph may return dict -> normalize to InterviewState using Pydantic
            if isinstance(result, dict):
                state = InterviewState.model_validate(result)
            else:
                state = result

            # Persist after each graph execution
            self._save_state(state)

            # Collect user input if required
            if state.awaiting_user_input and state.current_question_id:

                current_question = next(
                    (q for q in state.questions if q.id == state.current_question_id),
                    None,
                )

                if current_question:

                    self.output_renderer.render_question(current_question)

                    user_answer_text = self.input_adapter.get_answer(current_question)

                    # Compute attempt number for this question
                    existing_attempts = [
                        a for a in state.answers if a.question_id == current_question.id
                    ]

                    attempt_number = len(existing_attempts) + 1

                    state.answers.append(
                        Answer(
                            question_id=current_question.id,
                            content=user_answer_text,
                            attempt=attempt_number,
                        )
                    )

                    # Router owns semantic meaning.
                    # CLI only resets the flag after providing input.
                    state.awaiting_user_input = False

                    self._save_state(state)

            # Render execution result (if new)
            if state.execution_results:
                self.output_renderer.render_execution_result(
                    state.execution_results[-1]
                )

            # Render evaluation (if new)
            if state.evaluations:
                self.output_renderer.render_evaluation(state.evaluations[-1])

        # Interview completed
        self.output_renderer.render_completion(state.total_score)

        self._cleanup_state()

        return state
