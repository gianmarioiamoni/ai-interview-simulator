# interface/cli/interview_cli_runner.py

# InterviewCLIRunner
#
# Responsibility:
# - orchestrate loop
# - connect adapter and graph
# - do not write critical fields
# - do not do business logic
# - persist and restore interview state


import json
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

    def __init__(self) -> None:
        llm = DefaultLLMAdapter()
        self.graph = build_interview_graph(llm)

        self.input_adapter = CLIInputAdapter()
        self.output_renderer = CLIOutputRenderer()

    # ----------------------------
    # Persistence helpers
    # ----------------------------

    def _save_state(self, state: InterviewState) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(STATE_FILE, "w") as f:
            f.write(state.model_dump_json(indent=2))

    def _load_state(self) -> InterviewState | None:
        if not STATE_FILE.exists():
            return None

        with open(STATE_FILE, "r") as f:
            return InterviewState.model_validate_json(f.read())

    # ----------------------------
    # Main loop
    # ----------------------------

    def run(self, initial_state: InterviewState | None = None) -> InterviewState:

        # Try resume
        state = self._load_state() or initial_state

        if state is None:
            raise ValueError("Initial state required for new interview.")

        while state.progress != InterviewProgress.COMPLETED:

            # Invoke graph until it blocks waiting for user input
            state = self.graph.invoke(state)

            self._save_state(state)

            # If graph is waiting for user input, collect answer
            if state.awaiting_user_input:

                current_question = next(
                    (q for q in state.questions if q.id == state.current_question_id),
                    None,
                )

                if current_question is not None:

                    self.output_renderer.render_question(current_question)

                    user_answer_text = self.input_adapter.get_answer(current_question)

                    state.answers.append(
                        Answer(
                            question_id=current_question.id,
                            content=user_answer_text,
                        )
                    )

                    # Reset waiting flag (ownership: router owns flag,
                    # CLI just provides input)
                    state.awaiting_user_input = False

                    self._save_state(state)

            # Render execution result
            if state.execution_results:
                self.output_renderer.render_execution_result(
                    state.execution_results[-1]
                )

            # Render evaluation
            if state.evaluations:
                self.output_renderer.render_evaluation(state.evaluations[-1])

        # Interview completed
        self.output_renderer.render_completion(state.total_score)

        # Cleanup persisted state
        if STATE_FILE.exists():
            STATE_FILE.unlink()

        return state
