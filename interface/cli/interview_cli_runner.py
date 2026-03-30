# interface/cli/interview_cli_runner.py

from pathlib import Path

from app.runtime.interview_runtime import run_interview_graph

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from interface.cli.input_adapter import CLIInputAdapter
from interface.cli.output_renderer import CLIOutputRenderer
from infrastructure.llm.llm_adapter import DefaultLLMAdapter


STATE_FILE = Path("data/interview_state.json")


class CLIRunner:

    def __init__(self, llm=None) -> None:

        if llm is None:
            llm = DefaultLLMAdapter()

        # 🔥 FIX
        self.graph = run_interview_graph(llm=llm)

        self.input_adapter = CLIInputAdapter()
        self.output_renderer = CLIOutputRenderer()

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

    def run(self, initial_state: InterviewState | None = None) -> InterviewState:

        state = self._load_state() or initial_state

        if state is None:
            raise ValueError("Initial state required for new interview.")

        while state.progress != InterviewProgress.COMPLETED:

            result = run_interview_graph(state)

            if isinstance(result, dict):
                state = InterviewState.model_validate(result)
            else:
                state = result

            self._save_state(state)

            if state.awaiting_user_input and state.current_question_id:

                current_question = next(
                    (q for q in state.questions if q.id == state.current_question_id),
                    None,
                )

                if current_question:

                    self.output_renderer.render_question(current_question)

                    user_answer_text = self.input_adapter.get_answer(current_question)

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

                    state.awaiting_user_input = False

                    self._save_state(state)

            if state.execution_results:
                self.output_renderer.render_execution_result(
                    state.execution_results[-1]
                )

            if state.evaluations:
                self.output_renderer.render_evaluation(state.evaluations[-1])

        self.output_renderer.render_completion(state.total_score)

        self._cleanup_state()

        return state
