# services/narrative_service.py

import json
import logging
from typing import List, Dict

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from services.interview_evaluation.builders.narrative_control_builder import (
    NarrativeControlBuilder,
)
from domain.contracts.feedback.decision_explanation_schema import (
    DecisionExplanationSchema,
)

logger = logging.getLogger(__name__)


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
            balance_instruction = """
The candidate shows consistent performance across dimensions.
- Do NOT exaggerate differences
- Emphasize overall strength
"""
        elif balance_flag == "SLIGHTLY_UNEVEN":
            balance_instruction = """
The candidate shows strong overall performance with minor variation across areas.
- Highlight strengths
- Mention improvement areas without overemphasis
"""
        else:
            balance_instruction = """
There is a noticeable gap between strongest and weakest areas.
- Clearly highlight strengths and improvement areas
"""
        
        template = PromptLoader.load("narrative/executive_summary.txt")

        context = {
            "decision": decision,
            "overall_score": overall_score,
            "percentile": percentile,
            "strongest": strongest,
            "weakest": weakest,
            "strongest_score": strongest_score,
            "weakest_score": weakest_score,
            "balance_flag": balance_flag,
            "classification": classification_str,
            "balance_instruction": balance_instruction,
        }

        prompt = PromptRenderer.render(template, context)

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

        print("🔥 NARRATIVE SERVICE CALLED")
        print("🔥 NARRATIVE SERVICE GENERATING DECISION EXPLANATION")
        print("🔥 DECISION:", decision)
        print("🔥 DIMENSIONS:", dimensions)

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

        print("\n=== DECISION PROMPT ===")
        print(prompt)
        print("=== END ===\n")

        try:

            explanation = self._llm.invoke_json(
                prompt,
                schema=DecisionExplanationSchema
            )
            print("\n✅ PARSED EXPLANATION OBJECT:")
            print(explanation)
            print("TYPE:", type(explanation))

            return {
                "drivers": explanation.drivers,
                "blockers": explanation.blockers,
            }

        except Exception as e:
            logger.warning(f"decision_explanation_structured_failed: {e}")
            print("\n❌ DECISION EXPLANATION FAILED")
            print("ERROR:", e)

            # 🔥 CRITICAL DEBUG
            raw = self._llm.invoke(prompt)
            print("\n=== RAW FALLBACK LLM OUTPUT ===")
            print(raw.content)
            print("=== END RAW ===\n")

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

            if score >= 90:
                drivers.append(f"Strong capability in {name}")
            elif score >= 80:
                drivers.append(f"{name} is solid but not a differentiating strength")
            elif score >= 70:
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
