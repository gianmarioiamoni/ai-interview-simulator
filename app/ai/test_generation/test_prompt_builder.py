# app/ai/test_generation/test_prompt_builder.py

"""
Owns prompt construction for AI test case generation.

Mirrors the role of SQLPromptBuilder and CodingPromptBuilder in the
question-intelligence subsystem, keeping template loading and context
assembly out of AITestGenerator.
"""

import json

from domain.contracts.execution.coding_spec import CodingSpec
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer


class TestPromptBuilder:
    """
    Builds the rendered prompt string sent to the LLM for test generation.

    Stateless — safe to share across requests.
    """

    def build(
        self,
        problem: str,
        spec: CodingSpec,
        num_tests: int,
    ) -> str:
        template = PromptLoader.load("test_generation/ai_test_generator.txt")

        context = {
            "problem": problem,
            "entrypoint": spec.entrypoint,
            "parameters": json.dumps(spec.parameters),
            "num_tests": num_tests,
            "param_count": len(spec.parameters),
        }

        return PromptRenderer.render(template, context)
