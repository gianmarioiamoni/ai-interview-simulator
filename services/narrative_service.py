# services/narrative_service.py

from typing import List, Dict

import json
import re

from app.ports.llm_port import LLMPort


class NarrativeService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    # ---------------------------------------------------------
    # EXECUTIVE SUMMARY (ENTERPRISE)
    # ---------------------------------------------------------

    def generate_executive_summary(
        self,
        decision: str,
        overall_score: float,
        strongest: str,
        weakest: str,
        percentile: float,
    ) -> str:

        prompt = f"""
You are a senior hiring manager.

Write a concise executive summary (max 4 lines).

INPUT:
- Decision: {decision}
- Score: {overall_score}
- Strongest area: {strongest}
- Weakest area: {weakest}
- Percentile: {percentile}

RULES:
- Be decisive and professional
- No generic phrases
- Focus on hiring decision
"""

        response = self._llm.invoke(prompt)
        return response.content.strip()

    # ---------------------------------------------------------
    # DECISION EXPLANATION (DRIVERS / BLOCKERS)
    # ---------------------------------------------------------

    def generate_decision_explanation(
        self,
        decision: str,
        dimensions: List[Dict],
    ) -> Dict[str, List[str]]:

        prompt = f"""
            You are a senior technical hiring panel.

            Decision: {decision}

            Dimensions:
            {dimensions}

            TASK:
            - Identify key drivers (positive signals that support hiring)
            - Identify blockers (risks or weaknesses affecting hiring decision)

            RULES:
            - Each point must explain IMPACT on hiring decision
            - Be specific (mention score or implication)
            - Avoid generic statements

            OUTPUT FORMAT (STRICT JSON):
            {{
              "drivers": ["..."],
              "blockers": ["..."]
            }}
        """

        response = self._llm.invoke(prompt)

        try:
            parsed = self._extract_json(response.content)
            return {
                "drivers": parsed.get("drivers", []),
                "blockers": parsed.get("blockers", []),
            }
        except Exception:
            return {"drivers": [], "blockers": []}

    # ---------------------------------------------------------
    # DIMENSION NARRATIVE
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

    def _parse_bullets(self, text: str) -> List[str]:

        lines = text.split("\n")

        bullets = []
        for l in lines:
            l = l.strip("-• ").strip()
            if l:
                bullets.append(l)

        return bullets[:5]


    def _extract_json(self, text: str) -> Dict:

        try:
            return json.loads(text)
        except Exception:
            try:
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
            except Exception:
                pass

        return {}