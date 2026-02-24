# interface/cli/interview_cli_runner.py

# InterviewCLIRunner
#
# Responsibility:
# - orchestrate loop
# - connect adapter and graph
# - do not write critical fields
# - do not do business logic

from app.graph.interview_graph import build_interview_graph
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.answer import Answer

from interface.cli.input_adapter import CLIInputAdapter
from interface.cli.output_renderer import CLIOutputRenderer
from infrastructure.llm.llm_adapter import DefaultLLMAdapter


class CLIRunner:
    # Coordinates CLI interaction with the LangGraph engine

    def __init__(self) -> None:
        self.graph = build_interview_graph()
        self.input_adapter = CLIInputAdapter()
        self.output_renderer = CLIOutputRenderer()

    def run(self, initial_state: InterviewState) -> InterviewState:
        state = initial_state

        while state.progress != InterviewProgress.COMPLETED:

            # Invoke graph step
            state = self.graph.invoke(state)

            # If a question is active and no answer yet, collect input
            if state.current_question_id is not None:
                current_question = next(
                    (q for q in state.questions if q.id == state.current_question_id),
                    None,
                )

                if current_question is not None:
                    self.output_renderer.render_question(current_question)

                    user_answer_text = self.input_adapter.get_answer(current_question)

                    # Append answer without breaking ownership rules
                    state.answers.append(
                        Answer(
                            question_id=current_question.id, content=user_answer_text
                        )
                    )

            # Render execution result if present
            if state.execution_results:
                self.output_renderer.render_execution_result(
                    state.execution_results[-1]
                )

            # Render evaluation if present
            if state.evaluations:
                self.output_renderer.render_evaluation(state.evaluations[-1])

        # Final output
        self.output_renderer.render_completion(state.total_score)

        return state
