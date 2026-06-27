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

    Accepts an optional CodingDomainProfile to inject domain-specific
    edge-case hints into the hidden test generation prompt.
    """

    def build(
        self,
        problem: str,
        spec: CodingSpec,
        num_tests: int,
        domain_profile=None,
    ) -> str:
        template = PromptLoader.load("test_generation/ai_test_generator.txt")

        context = {
            "problem": problem,
            "entrypoint": spec.entrypoint,
            "parameters": json.dumps(spec.parameters),
            "num_tests": num_tests,
            "param_count": len(spec.parameters),
            "param_example": ", ".join(spec.parameters),
            "domain_hints_block": self._domain_hints_block(domain_profile),
        }

        return PromptRenderer.render(template, context)

    def _domain_hints_block(self, domain_profile) -> str:
        if domain_profile is None or not domain_profile.test_scenario_hints:
            return ""
        hints = ", ".join(domain_profile.test_scenario_hints)
        return (
            f"\nDOMAIN TEST HINTS (prefer these edge cases where applicable):\n"
            f"{hints}\n"
        )
