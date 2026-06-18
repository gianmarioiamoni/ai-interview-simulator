# tests/services/question_intelligence/test_sql_metadata_generation.py
"""
Tests for metadata-driven SQL generation:
- domains propagation to generate()
- difficulty_label propagation to generate()
- scenario_anchor propagation to generate()
- optional rendering (absent = no block in prompt)
- backward compatibility (existing calls unchanged)
"""

import json
import pytest
from unittest.mock import MagicMock

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.scenario_anchor import ScenarioAnchor
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator


_VALID_SQL_JSON = json.dumps(
    [
        {
            "prompt": "List all department names.",
            "reference_query": "SELECT name FROM departments",
            "test_cases": [
                {"expected_query": "SELECT name FROM departments", "ordered": False},
                {"expected_query": "SELECT d.name FROM departments d", "ordered": False},
            ],
        }
    ]
)


def _make_llm(json_str: str = _VALID_SQL_JSON) -> MagicMock:
    llm = MagicMock()
    response = MagicMock()
    response.content = json_str
    llm.invoke.return_value = response
    return llm


def _captured_prompt(llm: MagicMock) -> str:
    return llm.invoke.call_args[0][0]


# ── ScenarioAnchor enum ──────────────────────────────────────────────────────


class TestScenarioAnchorEnum:
    def test_all_values_present(self):
        values = {a.value for a in ScenarioAnchor}
        assert values == {
            "reporting",
            "optimization",
            "troubleshooting",
            "data_quality",
            "anti_pattern",
            "dml_pattern",
        }

    def test_str_enum(self):
        assert ScenarioAnchor.REPORTING == "reporting"
        assert ScenarioAnchor.ANTI_PATTERN == "anti_pattern"


# ── domains propagation ──────────────────────────────────────────────────────


class TestGenerateDomainsParam:
    def test_domains_appear_in_prompt(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            domains=["joins", "aggregation"],
        )
        prompt = _captured_prompt(llm)
        assert "DOMAIN FOCUS" in prompt
        assert "joins" in prompt
        assert "aggregation" in prompt

    def test_domains_block_mandatory_label(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            domains=["cte"],
        )
        prompt = _captured_prompt(llm)
        assert "mandatory" in prompt

    def test_no_domain_focus_when_domains_absent(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)
        prompt = _captured_prompt(llm)
        assert "DOMAIN FOCUS" not in prompt


# ── difficulty_label propagation ─────────────────────────────────────────────


class TestGenerateDifficultyLabelParam:
    def test_difficulty_label_appears_in_prompt(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            n=1,
            difficulty_label="hard",
        )
        prompt = _captured_prompt(llm)
        assert "DIFFICULTY TARGET" in prompt
        assert "HARD" in prompt

    def test_difficulty_label_uppercased(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            difficulty_label="intermediate",
        )
        prompt = _captured_prompt(llm)
        assert "INTERMEDIATE" in prompt

    def test_no_difficulty_block_when_absent(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)
        prompt = _captured_prompt(llm)
        assert "DIFFICULTY TARGET" not in prompt


# ── scenario_anchor propagation ──────────────────────────────────────────────


class TestGenerateScenarioAnchorParam:
    def test_scenario_anchor_appears_in_prompt(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            scenario_anchor=ScenarioAnchor.REPORTING,
        )
        prompt = _captured_prompt(llm)
        assert "SCENARIO FOCUS" in prompt
        assert "reporting" in prompt

    def test_scenario_anchor_optimization(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            scenario_anchor=ScenarioAnchor.OPTIMIZATION,
        )
        prompt = _captured_prompt(llm)
        assert "optimization" in prompt

    def test_scenario_anchor_anti_pattern(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            scenario_anchor=ScenarioAnchor.ANTI_PATTERN,
        )
        prompt = _captured_prompt(llm)
        assert "anti_pattern" in prompt

    def test_no_scenario_block_when_absent(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)
        prompt = _captured_prompt(llm)
        assert "SCENARIO FOCUS" not in prompt


# ── combined metadata ────────────────────────────────────────────────────────


class TestGenerateCombinedMetadata:
    def test_all_metadata_params_render_together(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            n=2,
            domains=["window_function", "cte"],
            difficulty_label="hard",
            scenario_anchor=ScenarioAnchor.TROUBLESHOOTING,
        )
        prompt = _captured_prompt(llm)
        assert "DOMAIN FOCUS" in prompt
        assert "window_function" in prompt
        assert "DIFFICULTY TARGET" in prompt
        assert "HARD" in prompt
        assert "SCENARIO FOCUS" in prompt
        assert "troubleshooting" in prompt


# ── backward compatibility ────────────────────────────────────────────────────


class TestGenerateBackwardCompatibility:
    def test_generate_without_new_params_succeeds(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        questions = gen.generate(
            role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1
        )
        assert isinstance(questions, list)

    def test_generate_with_only_theme_guidance_succeeds(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        questions = gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            theme_guidance="complex joins",
        )
        assert isinstance(questions, list)

    def test_no_new_blocks_when_all_params_absent(self):
        llm = _make_llm()
        gen = SQLQuestionGenerator(llm)
        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)
        prompt = _captured_prompt(llm)
        assert "DIFFICULTY TARGET" not in prompt
        assert "SCENARIO FOCUS" not in prompt
        assert "DOMAIN FOCUS" not in prompt
