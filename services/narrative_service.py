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
        evaluations=None,
        seniority_level: str = "mid",
        role: str = "backend engineer",
    ) -> str:

        readiness_map = {
            "hire": "Interview Ready",
            "lean_hire": "Nearly Ready",
            "lean_no_hire": "Needs Improvement",
            "no_hire": "Not Ready Yet",
        }
        readiness_label = readiness_map.get(decision, "Needs Improvement")

        tone = self._derive_tone(decision)
        template = PromptLoader.load("narrative/executive_summary.txt")

        context = {
            "decision": decision,
            "readiness_label": readiness_label,
            "overall_score": overall_score,
            "percentile": round(percentile),
            "strongest": strongest,
            "weakest": weakest,
            "strongest_score": strongest_score,
            "weakest_score": weakest_score,
            "tone": tone,
            "seniority_level": seniority_level,
            "role": role.replace("_", " ") if role else "engineer",
            "context_block": self._build_context_block(context_profile),
            "evidence_block": self._build_evidence_block(evaluations),
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
        cd = getattr(context_profile, "company_description", None)

        lines = []
        if bc is not None and bc.value != "generic":
            lines.append(f"Industry: {bc.value.upper()}")
        if jd and jd.strip():
            lines.append(f"Job Description: {jd.strip()[:300]}")
        if cd and cd.strip():
            lines.append(f"Company: {cd.strip()[:200]}")

        if not lines:
            return ""

        return "\n".join(lines) + "\n"

    def _build_evidence_block(self, evaluations) -> str:
        """Build a compact evidence summary from per-question evaluations.

        Extracts up to 3 notable strengths and up to 3 notable weaknesses
        across all questions for use in the executive summary prompt.
        """
        if not evaluations:
            return "No question-level evidence available."

        strengths = []
        weaknesses = []

        for ev in evaluations:
            for s in getattr(ev, "strengths", []) or []:
                if s and s not in strengths:
                    strengths.append(s)
                    if len(strengths) >= 4:
                        break
            for w in getattr(ev, "weaknesses", []) or []:
                if w and w not in weaknesses:
                    weaknesses.append(w)
                    if len(weaknesses) >= 4:
                        break
            if len(strengths) >= 4 and len(weaknesses) >= 4:
                break

        lines = []
        if strengths:
            lines.append("Observed strengths:")
            for s in strengths[:3]:
                lines.append(f"  - {s}")
        if weaknesses:
            lines.append("Observed gaps:")
            for w in weaknesses[:3]:
                lines.append(f"  - {w}")

        return "\n".join(lines) if lines else "No specific observations available."
