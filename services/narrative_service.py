# services/narrative_service.py

import json
import logging
import re
from typing import List, Dict

from app.ports.llm_port import LLMPort
from app.prompts.prompt_loader import PromptLoader

from services.interview_evaluation.builders.narrative_control_builder import (
    NarrativeControlBuilder,
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

        # -----------------------------------------------------
        # PREPARE TEMPLATE INPUT (NO MUTATION)
        # -----------------------------------------------------

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

        print("\n=== TEMPLATE START ===")
        print(template)
        print("=== TEMPLATE END ===\n")

        print("\n=== EXEC SUMMARY PAYLOAD ===")
        print(payload)
        print("=== END ===\n")

        # -----------------------------------------------------
        # BUILD PROMPT (NO SIDE EFFECTS)
        # -----------------------------------------------------

        prompt = template.format(
            decision=payload["decision"],
            overall_score=payload["overall_score"],
            percentile=payload["percentile"],
            strongest=payload["strongest"],
            strongest_score=payload["strongest_score"],
            weakest=payload["weakest"],
            weakest_score=payload["weakest_score"],
            balance_flag=payload["balance_flag"],
            classification=classification_str,
            balance_instruction=balance_instruction,
        )

        print("\n================ EXECUTIVE SUMMARY PROMPT ================\n")
        print(prompt)
        print("\n=========================================================\n")

        print("CALLING LLM FOR EXEC SUMMARY...")

        response = self._llm.invoke(prompt)

        content = (response.content or "").strip()

        print("\n================ EXECUTIVE SUMMARY RESPONSE ================\n")
        print("LEN:", len(content))
        print("RAW:", repr(content))
        print("\n=========================================================\n")

        if not content:
            print("EMPTY OUTPUT DETECTED")
            return ""

        return content

    # ---------------------------------------------------------
    # DECISION EXPLANATION
    # ---------------------------------------------------------

    def generate_decision_explanation(
        self,
        decision: str,
        dimensions: List[Dict],
    ) -> Dict[str, List[str]]:

        template = PromptLoader.load("narrative/decision_explanation.txt")

        dimensions_str = json.dumps(dimensions, indent=2)

        prompt = template.format(
            decision=decision,
            dimensions=dimensions_str,
        )

        print("\n=== DECISION PROMPT ===")
        print(prompt)
        print("=== END ===\n")

        # 👉 qui puoi migliorare dopo con invoke_json
        response = self._llm.invoke_json(prompt)

        print("\n=== DECISION EXPLANATION RAW ===")
        print(response.content)
        print("=== END ===\n")

        content = response.content.strip()

        if not content.startswith("{"):
            print("LLM did not return pure JSON")

        try:
            parsed = self._extract_json(content)

            return {
                "drivers": parsed.get("drivers", []),
                "blockers": parsed.get("blockers", []),
            }

        except Exception as e:
            print("Decision explanation parsing failed:", e)
            print("Raw LLM output:", content)

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

        prompt = f"""
Explain this performance dimension in 1 sentence.

Dimension: {name}
Score: {score}
Impact: {impact}

Be specific and professional.
"""

        response = self._llm.invoke(prompt)

        return response.content.strip()

    # ---------------------------------------------------------
    # UTILS
    # ---------------------------------------------------------

    def _extract_json(self, text: str) -> dict:

        text = re.sub(r"```json|```", "", text)

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found")

        return json.loads(match.group(0))

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
