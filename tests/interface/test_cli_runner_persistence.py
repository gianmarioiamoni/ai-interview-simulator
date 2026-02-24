# tests/interface/test_cli_runner_persistence.py

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import Question, QuestionType
from domain.contracts.interview_progress import InterviewProgress

from interface.cli.interview_cli_runner import CLIRunner
from tests.fakes.fake_llm import FakeLLM


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------


class DummyInputAdapter:
    def get_answer(self, question):
        return "Test answer"


class DummyOutputRenderer:
    def render_question(self, question):
        pass

    def render_execution_result(self, result):
        pass

    def render_evaluation(self, evaluation):
        pass

    def render_completion(self, score):
        pass


def build_minimal_state() -> InterviewState:
    question = Question(
        id="q1",
        area="backend",
        type=QuestionType.WRITTEN,
        prompt="Explain REST",
        difficulty=3,
    )

    return InterviewState(
        interview_id="test_1",
        role="Backend Engineer",
        company="TestCorp",
        questions=[question],
        current_question_id="q1",
    )


# ---------------------------------------------------
# Tests
# ---------------------------------------------------


def test_state_persistence_and_cleanup(tmp_path, monkeypatch):
    # Verifica:
    # - creazione file stato
    # - completamento intervista
    # - rimozione file finale

    state_file = tmp_path / "interview_state.json"

    monkeypatch.setattr(
        "interface.cli.interview_cli_runner.STATE_FILE",
        state_file,
    )

    fake_llm = FakeLLM(
        [
            "Humanized question",
            """
            {
                "score": 80,
                "feedback": "Good",
                "clarification_needed": false,
                "follow_up_question": null
            }
            """,
        ]
    )

    runner = CLIRunner(fake_llm)
    runner.input_adapter = DummyInputAdapter()
    runner.output_renderer = DummyOutputRenderer()

    initial_state = build_minimal_state()

    final_state = runner.run(initial_state)

    # File deve essere stato rimosso a fine intervista
    assert not state_file.exists()

    # Stato completato
    assert final_state.progress == InterviewProgress.COMPLETED


def test_state_file_created_during_execution(tmp_path, monkeypatch):
    # Verifica che il file venga creato durante esecuzione

    state_file = tmp_path / "interview_state.json"

    monkeypatch.setattr(
        "interface.cli.interview_cli_runner.STATE_FILE",
        state_file,
    )

    fake_llm = FakeLLM(
        [
            "Humanized question",
            """
            {
                "score": 50,
                "feedback": "Needs improvement",
                "clarification_needed": false,
                "follow_up_question": null
            }
            """,
        ]
    )

    runner = CLIRunner(fake_llm)
    runner.input_adapter = DummyInputAdapter()
    runner.output_renderer = DummyOutputRenderer()

    state = build_minimal_state()

    # Esegui un ciclo e salva manualmente
    state = runner.graph.invoke(state)
    runner._save_state(state)

    assert state_file.exists()

    loaded = InterviewState.model_validate_json(state_file.read_text())

    assert loaded.interview_id == state.interview_id


def test_resume_from_existing_state(tmp_path, monkeypatch):
    # Verifica resume automatico da file esistente

    state_file = tmp_path / "interview_state.json"

    monkeypatch.setattr(
        "interface.cli.interview_cli_runner.STATE_FILE",
        state_file,
    )

    state = build_minimal_state()

    # Simula stato salvato precedentemente
    state_file.write_text(state.model_dump_json())

    fake_llm = FakeLLM(
        [
            "Humanized question",
            """
            {
                "score": 90,
                "feedback": "Excellent",
                "clarification_needed": false,
                "follow_up_question": null
            }
            """,
        ]
    )

    runner = CLIRunner(fake_llm)
    runner.input_adapter = DummyInputAdapter()
    runner.output_renderer = DummyOutputRenderer()

    final_state = runner.run()

    assert final_state.progress == InterviewProgress.COMPLETED
