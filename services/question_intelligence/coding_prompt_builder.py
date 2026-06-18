# services/question_intelligence/coding_prompt_builder.py

import random

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.config.settings import settings


_JSON_OUTPUT_CONTRACT = """
Return STRICT JSON array:

[
  {
    "prompt": "...",

    "coding_spec": {
      "type": "function",
      "entrypoint": "function_name",
      "parameters": ["param1", "param2"]
    },

    "visible_tests": [
      {
        "args": [...],
        "expected": ...
      }
    ]
  }
]
"""


class CodingPromptBuilder:
    """
    Builds LLM prompts for coding question generation and enrichment.
    Owns the JSON output contract definition.

    Accepts an optional CodingDomainProfile to inject domain vocabulary,
    scenario anchors, and framing blocks when feature flags are enabled.
    """

    def __init__(self, domain_profile=None) -> None:
        self._domain_profile = domain_profile

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> str:

        template = PromptLoader.load("generation/coding_question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "level": level,
                "role": role,
                "theme_block": self._theme_block(theme_guidance),
                "cd_block": self._cd_block(company_description),
                "jd_block": self._jd_block(job_description),
                "domain_framing_block": self._domain_framing_block(),
                "vocabulary_block": self._vocabulary_block(),
                "scenario_block": self._scenario_block(),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
            },
        )

    def build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> str:

        template = PromptLoader.load("generation/coding_question_enrichment.txt")

        return PromptRenderer.render(
            template,
            {
                "seed_prompt": seed_prompt,
                "level": level,
                "role": role,
                "theme_block": self._theme_block(theme_guidance),
                "cd_block": self._cd_block(company_description),
                "jd_block": self._jd_block(job_description),
                "domain_framing_block": self._domain_framing_block(),
                "vocabulary_block": self._vocabulary_block(),
                "scenario_block": self._scenario_block(),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
            },
        )

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _theme_block(self, theme_guidance: str | None) -> str:
        if theme_guidance:
            return f"\nTHEME GUIDANCE:\n{theme_guidance}\n"
        return ""

    def _jd_block(self, job_description: str | None) -> str:
        if not job_description or not job_description.strip():
            return ""
        truncated = job_description.strip()[:settings.job_description_max_chars]
        return f"\nJOB DESCRIPTION CONTEXT (guidance only — do not override domain or difficulty):\n{truncated}\n"

    def _cd_block(self, company_description: str | None) -> str:
        if not company_description or not company_description.strip():
            return ""
        truncated = company_description.strip()[:settings.company_description_max_chars]
        return f"\nCOMPANY DESCRIPTION (scenario framing only — do not change domain, difficulty, or seniority):\n{truncated}\n"

    def _domain_framing_block(self) -> str:
        if not settings.coding_domain_profile_enabled:
            return ""
        profile = self._domain_profile
        if profile is None or profile.context_summary is None:
            return ""
        return (
            f"\nDOMAIN FRAMING (mandatory — frame the problem narrative accordingly):\n"
            f"{profile.context_summary}\n"
        )

    def _vocabulary_block(self) -> str:
        if not settings.coding_domain_vocabulary_enabled:
            return ""
        profile = self._domain_profile
        if profile is None or not profile.vocabulary_hint:
            return ""
        terms = ", ".join(profile.vocabulary_hint)
        return (
            f"\nDOMAIN VOCABULARY (incorporate where natural — do not force):\n"
            f"{terms}\n"
        )

    def _scenario_block(self) -> str:
        if not settings.coding_scenario_anchor_enabled:
            return ""
        profile = self._domain_profile
        if profile is None or not profile.scenario_anchor_pool:
            return ""
        anchor = random.choice(profile.scenario_anchor_pool)
        return (
            f"\nSCENARIO ANCHOR (base the problem around this scenario):\n"
            f"{anchor}\n"
        )
