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
        strongest_score: float,
        weakest_score: float,
    ) -> str:

        is_balanced = False
        if strongest_score is not None and weakest_score is not None:
            if (abs(strongest_score - weakest_score) < 10):
                is_balanced = True
        balance_instruction = ""

        if is_balanced: 
            balance_instruction = f"""
            The candidate shows balanced performance across dimensions.
            - Do NOT say "no strengths or weaknesses"
            - Do NOT exaggerate differences
            - Use phrasing like "well-balanced", "consistent across areas"
            """
        else:   
            balance_instruction = """
            Highlight strongest and weakest areas clearly.
            Explain strengths and areas for improvement.
            """

        balance_flag = "BALANCED" if is_balanced else "UNBALANCED"

        prompt = f"""
            You are a senior technical interviewer writing an executive summary.

            Write a concise executive summary (max 4 lines).

            INPUT:
            - Decision: {decision}
            - Score: {overall_score}
            - Strongest area: {strongest}
            - Weakest area: {weakest}
            - Performance type: {balance_flag}
            - Percentile: {percentile}
            - Strongest score: {strongest_score}
            - Weakest score: {weakest_score}

            RULES:
            - Be decisive and professional
            - No generic phrases
            - Focus on hiring decision

            {balance_instruction}

            STRICT CONSTRAINTS:
            - NEVER say "no strengths or weaknesses"
            - ALWAYS reflect strongest and weakest areas OR balanced performance correctly
            
            If the weakest score is >= 80:
                - DO NOT use words like "gap", "weak", or "deficiency"
                - Use softer language like "minor area for improvement"
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

        print("DEBUG DIMENSIONS:", dimensions)

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

        Additional rules:
        - If a dimension score is >= 80:
            - DO NOT describe it as "weak"
            - Use "area for improvement" instead

        - Use "weak" ONLY if score < 70
        - Do not be generic


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
