# services/narrative_service.py

import json
import logging
import re
from typing import List, Dict

from app.ports.llm_port import LLMPort

from app.prompts.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


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

        prompt_template = PromptLoader.load("narrative/executive_summary.txt")
        prompt = prompt_template.format(
            decision=decision,
            overall_score=overall_score,
            strongest=strongest,
            weakest=weakest,
            percentile=percentile,
            strongest_score=strongest_score,
            weakest_score=weakest_score,
            balance_flag=balance_flag,
            balance_instruction=balance_instruction,
        )

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

        template = PromptLoader.load("narrative/decision_explanation.txt")
        logger.debug("DECISION EXPLANATION TEMPLATE: %s", template)

        # serialize dimensions to string
        dimensions_str = json.dumps(dimensions, indent=2)

        prompt = template.format(
            decision=decision,
            dimensions=dimensions_str,
        )
        logger.debug("DECISION EXPLANATION PROMPT: %s", prompt)

        response = self._llm.invoke(prompt)
        logger.debug("DECISION EXPLANATION RESPONSE: %s", response.content)

        try:
            parsed = self._extract_json(response.content)
            return {
                "drivers": parsed.get("drivers", []),
                "blockers": parsed.get("blockers", []),
            }
        except Exception as e:
            print("DECISION EXPLANATION PARSE ERROR:", e)
            print("RAW RESPONSE:", response.content)
            logger.error("DECISION EXPLANATION PARSE ERROR: %s", e)

            return {
                "drivers": ["Strong performance in key areas"], 
                "blockers": ["Area for improvement identified"]}

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

        print("------ RAW LLM RESPONSE ------")
        print(response.content)
        print("------ END RESPONSE ------")
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

    def _extract_json(self, text: str) -> dict:

        # Remove markdown code blocks if present
        text = re.sub(r"```json|```", "", text)

        # Extract JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found in LLM output")

        json_str = match.group(0)

        return json.loads(json_str)
