# services/narrative_service.py

import json
from typing import List, Dict, Optional

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from services.interview_evaluation.builders.narrative_control_builder import (
    NarrativeControlBuilder,
)
from domain.contracts.feedback.decision_explanation_schema import (
    DecisionExplanationSchema,
)
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import NARRATIVE_GENERATION
from infrastructure.config.evaluation import (
    NARRATIVE_FALLBACK_DRIVER_STRONG,
    NARRATIVE_FALLBACK_DRIVER_SOLID,
    NARRATIVE_FALLBACK_BLOCKER_DEVELOPMENT,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class NarrativeService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ---------------------------------------------------------
    # EXECUTIVE SUMMARY
    # ---------------------------------------------------------

    def generate_executive_summary(
        self,
        decision: str,
        overall_score: float,
        strongest: str,
        weakest: str,
        percentile: float,
        strongest_score: float,
        weakest_score: float,
        context_profile=None,
    ) -> str:

        builder = NarrativeControlBuilder()

        payload = builder.build_summary_payload(
            decision=decision,
            overall_score=overall_score,
            percentile=percentile,
            dimensions=[
                {"name": strongest, "score": strongest_score},
                {"name": weakest, "score": weakest_score},
            ],
        )

        if not payload:
            logger.error("Empty narrative payload")
            return "Evaluation completed with insufficient data."

        classification_str = json.dumps(payload["classification"], indent=2)
        balance_flag = payload["balance_flag"]

        if balance_flag == "BALANCED":
            balance_instruction = PromptLoader.load(
                "reporting/balance_instruction_balanced.txt"
            )
        elif balance_flag == "SLIGHTLY_UNEVEN":
            balance_instruction = PromptLoader.load(
                "reporting/balance_instruction_slightly_uneven.txt"
            )
        else:
            balance_instruction = PromptLoader.load(
                "reporting/balance_instruction_uneven.txt"
            )
        tone = self._derive_tone(decision)
        template = PromptLoader.load("narrative/executive_summary.txt")

        context = {
            "decision": decision,
            "overall_score": overall_score,
            "percentile": percentile,
            "strongest": strongest,
            "weakest": weakest,
            "strongest_score": strongest_score,
            "weakest_score": weakest_score,
            "classification": classification_str,
            "balance_instruction": balance_instruction,
            "tone": tone,
            "context_block": self._build_context_block(context_profile),
        }

        prompt = PromptRenderer.render(template, context)

        with LLMOperationContext.scope(NARRATIVE_GENERATION):
            response = self._llm.invoke(prompt)
        content = (response.content or "").strip()

        if not content:
            return ""

        return content

    # ---------------------------------------------------------
    # DECISION EXPLANATION
    # ---------------------------------------------------------

    def generate_decision_explanation(
        self,
        decision: str,
        dimensions: List[Dict],
        dimension_signals: Dict[str, float] | None = None, 
    ) -> Dict[str, List[str]]:

        logger.debug("generate_decision_explanation: decision=%s", decision)

        template = PromptLoader.load("narrative/decision_explanation.txt")

        dimensions_str = json.dumps(dimensions, indent=2)

        signals_str = json.dumps(dimension_signals or {}, indent=2)

        tone = self._derive_tone(decision)

        context = {
            "decision": decision,
            "dimensions": dimensions_str,
            "signals": signals_str,
            "tone": tone,
        }

        prompt = PromptRenderer.render(template, context)

        try:

            with LLMOperationContext.scope(NARRATIVE_GENERATION):
                explanation = self._llm.invoke_json(
                    prompt,
                    schema=DecisionExplanationSchema
                )

            return {
                "drivers": explanation.drivers,
                "blockers": explanation.blockers,
            }

        except Exception as e:
            logger.warning("decision_explanation_structured_failed: %s", e)
            return self._deterministic_fallback(dimensions)

    # ---------------------------------------------------------
    # DIMENSION EXPLANATION
    # ---------------------------------------------------------

    def generate_dimension_explanation(
        self,
        name: str,
        score: float,
        impact: str,
    ) -> str:

        template = PromptLoader.load("narrative/dimension_explanation.txt")

        context = {
            "name": name,
            "score": score,
            "impact": impact,
        }

        prompt = PromptRenderer.render(template, context)

        with LLMOperationContext.scope(NARRATIVE_GENERATION):
            response = self._llm.invoke(prompt)

        return (response.content or "").strip()

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    def _deterministic_fallback(self, dimensions):

        drivers = []
        blockers = []

        for d in dimensions:
            try:
                name = d["name"]
                score = d["score"]
            except Exception:
                continue

            if score >= NARRATIVE_FALLBACK_DRIVER_STRONG:
                drivers.append(f"Strong capability in {name}")
            elif score >= NARRATIVE_FALLBACK_DRIVER_SOLID:
                drivers.append(f"{name} is solid but not a differentiating strength")
            elif score >= NARRATIVE_FALLBACK_BLOCKER_DEVELOPMENT:
                blockers.append(f"{name} requires further development")
            else:
                blockers.append(f"Weak performance in {name}")

        return {
            "drivers": drivers[:2] or ["Overall solid performance"],
            "blockers": blockers[:2] or ["Minor areas for improvement"],
        }


    def _derive_tone(self, decision: str) -> str:

        if decision in ["no_hire", "lean_no_hire"]:
            return "critical"

        if decision in ["hire", "strong_hire"]:
            return "positive"

        return "balanced"

    # ---------------------------------------------------------
    # CONTEXT BLOCK
    # ---------------------------------------------------------

    def _build_context_block(self, context_profile) -> str:
        """Build an industry/role context snippet for narrative prompts.

        Returns an empty string for generic context so existing behaviour
        is fully preserved when no JD/CD is supplied.
        """
        if context_profile is None:
            return ""

        bc = getattr(context_profile, "business_context", None)
        jd = getattr(context_profile, "job_description", None)

        if bc is None or bc.value == "generic":
            return ""

        lines = [f"Industry Context: {bc.value.upper()}"]
        if jd and jd.strip():
            lines.append(f"Role Context: {jd.strip()[:300]}")

        return "\n".join(lines) + "\n"
