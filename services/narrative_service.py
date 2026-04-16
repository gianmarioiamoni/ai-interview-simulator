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
        You are a senior technical interviewer.

        Decision: {decision}

        Candidate performance by dimension:
        {dimensions}

        Task:
        Explain the hiring decision.

        Return JSON with:
        - drivers: key strengths supporting the decision
        - blockers: key weaknesses preventing hiring

        Rules:
        - Always return at least 1 driver and 1 blocker
        - Be specific and reference dimensions when possible
        - Drivers must explain why the candidate could be hired
        - Blockers must explain why the candidate is not fully suitable
        - If the decision is negative, blockers should be stronger than drivers
        - Do not be generic (avoid "overall performance is good")

        Output format:
        {
          "drivers": [...],
          "blockers": [...]
        }
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
